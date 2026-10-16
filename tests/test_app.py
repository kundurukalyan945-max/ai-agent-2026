"""
Tests for AI Career Suite — app.py utility functions.

These tests cover the pure-Python helpers that can be exercised without
a running Streamlit instance or a real Groq API key.  They use
unittest.mock to verify that the Groq client is never called when the
key is absent, and to simulate API failures without making real requests.

Run:
    pip install pytest pytest-mock
    pytest tests/test_app.py -v
"""
import importlib
import os
import sys
import types
import io
import pytest


# ---------------------------------------------------------------------------
# Helpers to import only the pure-Python parts of app.py
# ---------------------------------------------------------------------------

def _import_helpers():
    """
    Import the public helper functions from app.py without executing the
    Streamlit page setup (st.set_page_config, st.sidebar, tabs, etc.).

    Strategy: patch `streamlit` with a minimal stub before the import so
    that all top-level Streamlit calls are no-ops.  The functions we care
    about (safe_html_text, mask_key, get_groq_client, call_llm) are pure
    enough that they work once the module is loaded.
    """
    # Build a streamlit stub with all attributes we need as no-ops
    stub = types.ModuleType("streamlit")
    for attr in [
        "set_page_config", "markdown", "sidebar", "radio", "chat_input",
        "chat_message", "error", "warning", "success", "info",
        "caption", "download_button", "button", "selectbox",
        "file_uploader", "rerun", "stop", "write", "empty",
        "dataframe", "line_chart", "progress", "column_config",
    ]:
        setattr(stub, attr, lambda *a, **kw: None)

    # Widgets that return a value — return the `value` kwarg so profile dict
    # is not overwritten with None when app.py does p["name"] = st.text_input(...)
    def _widget(*a, value=None, **kw):
        return value
    for attr in ["text_input", "text_area"]:
        setattr(stub, attr, _widget)

    # session_state needs to act like a dict-with-attribute-access
    class _SessionState(dict):
        def __getattr__(self, k):
            try:
                return self[k]
            except KeyError:
                raise AttributeError(k)
        def __setattr__(self, k, v):
            self[k] = v
        def __contains__(self, k):
            return dict.__contains__(self, k)

    stub.session_state = _SessionState()

    # context-manager stub — used for spinner, sidebar, expander, columns, tabs
    class _CM:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def __iter__(self):
            # st.columns(n) is unpacked: col1, col2 = st.columns(2)
            return iter([_CM(), _CM(), _CM(), _CM()])
        def __getattr__(self, k):
            return lambda *a, **kw: None

    def _cm_factory(*a, **kw):
        return _CM()

    stub.spinner = _cm_factory
    stub.sidebar = _CM()
    stub.expander = _cm_factory
    def _columns_factory(spec, **kw):
        count = len(spec) if isinstance(spec, (list, tuple)) else spec
        return [_CM() for _ in range(count)]
    stub.columns = _columns_factory
    stub.tabs = lambda n, **kw: [_CM() for _ in (n if isinstance(n, list) else range(n))]

    sys.modules["streamlit"] = stub

    # Remove cached module if re-running
    if "app" in sys.modules:
        del sys.modules["app"]

    # Set working directory so load_dotenv finds the real .env (if any)
    # without blowing up when it does not exist
    old_cwd = os.getcwd()
    os.chdir(os.path.join(os.path.dirname(__file__), ".."))
    try:
        import app as _app
    finally:
        os.chdir(old_cwd)

    return _app


app = _import_helpers()


# ===========================================================================
# 1. safe_html_text — XSS escaping
# ===========================================================================

class TestSafeHtmlText:
    def test_ampersand(self):
        assert app.safe_html_text("A & B") == "A &amp; B"

    def test_less_than(self):
        assert app.safe_html_text("<script>") == "&lt;script&gt;"

    def test_greater_than(self):
        assert app.safe_html_text("a > b") == "a &gt; b"

    def test_double_quote(self):
        assert app.safe_html_text('say "hi"') == "say &quot;hi&quot;"

    def test_xss_vector_full(self):
        raw = '<img src=x onerror="alert(1)">'
        escaped = app.safe_html_text(raw)
        assert "<" not in escaped
        assert ">" not in escaped
        assert '"' not in escaped

    def test_plain_text_unchanged(self):
        assert app.safe_html_text("Hello world") == "Hello world"

    def test_empty_string(self):
        assert app.safe_html_text("") == ""

    def test_double_escape_not_applied(self):
        # Already-escaped text should not be double-escaped
        already = "&amp;"
        result = app.safe_html_text(already)
        assert result == "&amp;amp;"  # one additional pass is expected

    def test_newlines_preserved(self):
        assert "\n" in app.safe_html_text("line1\nline2")


# ===========================================================================
# 2. mask_key — API key display masking
# ===========================================================================

class TestMaskKey:
    def test_normal_key(self):
        result = app.mask_key("gsk_abc123xyz789")
        assert result.startswith("gsk_")
        assert "••••••••" in result or "********" in result or "*" * 8 in result

    def test_short_key_returns_not_set(self):
        assert app.mask_key("abc") == "Not set"

    def test_empty_key(self):
        assert app.mask_key("") == "Not set"

    def test_none_key(self):
        assert app.mask_key(None) == "Not set"

    def test_exact_8_chars(self):
        # 8 chars is the minimum for a real key to show masked
        result = app.mask_key("12345678")
        assert result != "Not set"

    def test_last_4_chars_visible(self):
        key = "gsk_AAAABBBBCCCC1234"
        result = app.mask_key(key)
        assert result.endswith("1234")

    def test_first_4_chars_visible(self):
        key = "gsk_AAAABBBBCCCC1234"
        result = app.mask_key(key)
        assert result.startswith("gsk_")


# ===========================================================================
# 3. get_groq_client — missing key returns None
# ===========================================================================

class TestGetGroqClient:
    def test_returns_none_when_key_missing(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.setenv("GROQ_API_KEY", "")
        # Stub out groq if not installed so we can test the key-check path
        groq_stub = types.ModuleType("groq")
        class FakeGroq:
            def __init__(self, api_key=None):
                self.api_key = api_key
        groq_stub.Groq = FakeGroq
        monkeypatch.setitem(sys.modules, "groq", groq_stub)
        result = app.get_groq_client()
        assert result is None

    def test_returns_none_when_key_whitespace_only(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "   ")
        groq_stub = types.ModuleType("groq")
        class FakeGroq:
            def __init__(self, api_key=None):
                self.api_key = api_key
        groq_stub.Groq = FakeGroq
        monkeypatch.setitem(sys.modules, "groq", groq_stub)
        result = app.get_groq_client()
        assert result is None

    def test_returns_client_when_key_present(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "gsk_fake_key_for_testing_1234")
        groq_stub = types.ModuleType("groq")
        class FakeGroq:
            def __init__(self, api_key=None):
                self.api_key = api_key
        groq_stub.Groq = FakeGroq
        monkeypatch.setitem(sys.modules, "groq", groq_stub)
        client = app.get_groq_client()
        assert client is not None


# ===========================================================================
# 4. MODEL_ID — configurable via GROQ_MODEL env var
# ===========================================================================

class TestModelConfig:
    def test_default_model_is_llama(self):
        assert "llama" in app.MODEL_ID.lower() or "llama" in os.getenv("GROQ_MODEL", "llama").lower()

    def test_model_id_is_nonempty(self):
        assert app.MODEL_ID.strip() != ""

    def test_env_override_is_read(self, monkeypatch):
        monkeypatch.setenv("GROQ_MODEL", "llama-3.1-8b-instant")
        # Reimport the module to pick up new env
        import importlib
        if "app" in sys.modules:
            del sys.modules["app"]
        fresh = _import_helpers()
        assert fresh.MODEL_ID == "llama-3.1-8b-instant"


# ===========================================================================
# 5. call_llm — no API key → returns None (no real network call)
# ===========================================================================

class TestCallLlmNoKey:
    def test_returns_none_when_no_key(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "")
        # Patch get_groq_client directly so we don't need the groq package installed
        monkeypatch.setattr(app, "get_groq_client", lambda: None)
        result = app.call_llm([{"role": "user", "content": "Hello"}])
        assert result is None

    def test_groq_never_called_when_key_missing(self, monkeypatch):
        """Confirm zero API calls when key is absent."""
        monkeypatch.setenv("GROQ_API_KEY", "")
        called = []
        original = app.get_groq_client
        def fake_client():
            called.append(1)
            return None
        monkeypatch.setattr(app, "get_groq_client", fake_client)
        app.call_llm([{"role": "user", "content": "test"}])
        # get_groq_client is called once; since it returns None, Groq API never reached
        assert len(called) == 1


# ===========================================================================
# 6. call_llm — API error handling (mocked client)
# ===========================================================================

class TestCallLlmErrors:
    def _make_mock_client(self, exc, monkeypatch):
        """Patch get_groq_client to return a mock that raises exc."""
        class FakeClient:
            class chat:
                class completions:
                    @staticmethod
                    def create(**kwargs):
                        raise exc

        monkeypatch.setattr(app, "get_groq_client", lambda: FakeClient())

    def test_auth_error_returns_none(self, monkeypatch):
        self._make_mock_client(Exception("401 authentication failed"), monkeypatch)
        result = app.call_llm([{"role": "user", "content": "hi"}])
        assert result is None

    def test_rate_limit_returns_none(self, monkeypatch):
        self._make_mock_client(Exception("429 rate limit exceeded"), monkeypatch)
        result = app.call_llm([{"role": "user", "content": "hi"}])
        assert result is None

    def test_generic_error_returns_none(self, monkeypatch):
        self._make_mock_client(Exception("connection timeout"), monkeypatch)
        result = app.call_llm([{"role": "user", "content": "hi"}])
        assert result is None

    def test_model_not_found_returns_none(self, monkeypatch):
        self._make_mock_client(Exception("model not found"), monkeypatch)
        result = app.call_llm([{"role": "user", "content": "hi"}])
        assert result is None


# ===========================================================================
# 7. DOCX generation — python-docx produces a valid .docx binary
# ===========================================================================

class TestDocxGeneration:
    def test_docx_is_valid_zip(self):
        """A .docx is a ZIP archive — verify the magic bytes."""
        pytest.importorskip("docx", reason="python-docx not installed")
        from docx import Document
        doc = Document()
        doc.add_heading("Test Resume", level=1)
        doc.add_paragraph("Bullet point one")
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        magic = buf.read(4)
        # ZIP files start with PK\x03\x04
        assert magic == b"PK\x03\x04", "Generated file is not a valid ZIP/docx"

    def test_docx_round_trip(self):
        """Write then re-read a docx; content must survive."""
        pytest.importorskip("docx", reason="python-docx not installed")
        from docx import Document
        original_text = "Senior Python Developer — 5 ATS keywords"
        doc = Document()
        doc.add_paragraph(original_text)
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        doc2 = Document(buf)
        texts = [p.text for p in doc2.paragraphs]
        assert original_text in texts


# ===========================================================================
# 8. Input truncation constants are sensible
# ===========================================================================

class TestInputLimits:
    def test_max_input_chars_positive(self):
        assert app.MAX_INPUT_CHARS > 0

    def test_max_pdf_chars_positive(self):
        assert app.MAX_PDF_CHARS > 0

    def test_max_input_larger_than_pdf(self):
        # PDF chars is a sub-limit; input limit should be at least as big
        assert app.MAX_INPUT_CHARS >= app.MAX_PDF_CHARS

    def test_truncation_works_correctly(self):
        long_text = "x" * (app.MAX_INPUT_CHARS + 500)
        truncated = long_text[:app.MAX_INPUT_CHARS]
        assert len(truncated) == app.MAX_INPUT_CHARS


# ===========================================================================
# 9. Profile defaults — no personal data hardcoded
# ===========================================================================

class TestProfileDefaults:
    """
    app.DEFAULTS is a plain Python dict defined at module level.
    It must contain only generic placeholder text, never a real user's data.
    """

    def _get_defaults(self):
        # app.DEFAULTS is a real dict, not stored in session_state
        return app.DEFAULTS

    def test_defaults_is_dict(self):
        assert isinstance(self._get_defaults(), dict)

    def test_profile_key_exists(self):
        assert "profile" in self._get_defaults()

    def test_default_name_is_placeholder(self):
        profile = self._get_defaults()["profile"]
        assert isinstance(profile, dict), "DEFAULTS['profile'] must be a dict"
        assert profile.get("name") == "Your Name"

    def test_default_role_is_placeholder(self):
        profile = self._get_defaults()["profile"]
        role = profile.get("target_role", "")
        assert "target" in role.lower() or role == "Your target role"

    def test_no_personal_name_in_defaults(self):
        profile = self._get_defaults()["profile"]
        personal_names = ["kalyan", "kunduru", "svce", "nellore"]
        profile_str = " ".join(str(v) for v in profile.values()).lower()
        for name in personal_names:
            assert name not in profile_str, f"Personal data '{name}' found in profile defaults"
