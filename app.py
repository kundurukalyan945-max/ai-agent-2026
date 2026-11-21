"""
AI Career Suite — Streamlit application
Model: llama-3.3-70b-versatile via Groq
Config: GROQ_API_KEY environment variable (or .env file)
"""
import streamlit as st
from dotenv import load_dotenv
import os
import json
import io
import hmac
from datetime import datetime

import pandas as pd

from career_agent import (
    add_job, create_approval, decide_approval, get_profile, list_approvals,
    list_audit_events, list_jobs, save_profile, database_backend,
)
from career_agent.matching import score_job
from career_agent.happenstance import (
    HappenstanceError, connection_status, create_network_search,
    flatten_search_results, get_network_search, get_usage, referral_search_prompt,
)

load_dotenv()

# ──────────────────────────────────────────────────────────
# CONFIGURATION — centralised so it's easy to update
# ──────────────────────────────────────────────────────────
def get_setting(name: str, default: str = "") -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        secret_value = st.secrets.get(name, default)
        return str(secret_value).strip() if secret_value is not None else default
    except Exception:
        return default


MODEL_ID = get_setting("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_INPUT_CHARS = 8_000     # truncate large inputs before sending
MAX_PDF_CHARS = 4_000       # truncate extracted PDF text
API_TIMEOUT = 30            # seconds

def get_groq_client():
    """Return a Groq client or None if the key is missing."""
    from groq import Groq
    key = get_setting("GROQ_API_KEY")
    if not key:
        return None
    return Groq(api_key=key)


# ──────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Career Suite",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────
# SESSION STATE INIT
# ──────────────────────────────────────────────────────────
DEFAULTS: dict = {
    "messages": [],
    "score_history": [],
    "theme": "dark",
    "last_resume": None,
    "job_results": None,
    "profile": {
        "name": "Your Name",
        "education": "Degree, University, Year, GPA (edit in Settings)",
        "skills": "List your skills here (edit in Settings)",
        "project": "Your key project (edit in Settings)",
        "target_role": "Your target role",
        "target_location": "Your target city",
    },
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ──────────────────────────────────────────────────────────
# THEME TOKENS
# ──────────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "bg": "#0B0E11", "bg_card": "#14181D", "border": "#262C33",
        "accent": "#4A90D9", "accent_dim": "#4A90D922", "text": "#E8EAED",
        "text_dim": "#8A919C", "text_faint": "#565D66", "green": "#3DD68C",
        "btn_text": "#FFFFFF"
    },
    "light": {
        "bg": "#FAF8F5", "bg_card": "#FFFFFF", "border": "#E4E0D8",
        "accent": "#2563EB", "accent_dim": "#2563EB18", "text": "#1A1A1A",
        "text_dim": "#5C5850", "text_faint": "#8C887E", "green": "#1F8C5C",
        "btn_text": "#FFFFFF"
    }
}
T = THEMES[st.session_state.theme]

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;500;600;700;800&display=swap');

    .stApp {{ background: {T['bg']}; }}
    * {{ font-family: 'Inter', sans-serif; }}
    code, .mono {{ font-family: 'JetBrains Mono', monospace !important; }}

    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{ padding-top: 2rem; max-width: 1100px; }}

    .suite-header {{ display: flex; align-items: baseline; gap: 14px; margin-bottom: 2px; }}
    .suite-mark {{ color: {T['accent']}; font-family: 'JetBrains Mono', monospace; font-size: 28px; font-weight: 700; }}
    .suite-title {{ font-size: 30px; font-weight: 800; color: {T['text']}; letter-spacing: -0.5px; }}
    .suite-sub {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; color: {T['text_faint']}; margin-bottom: 28px; margin-top: 4px; letter-spacing: 0.3px; }}

    .panel-head {{ display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }}
    .panel-tag {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; color: {T['accent']}; background: {T['accent_dim']}; padding: 3px 9px; border-radius: 5px; font-weight: 700; letter-spacing: 0.5px; }}
    .panel-title {{ font-size: 20px; font-weight: 700; color: {T['text']}; }}
    .panel-desc {{ color: {T['text_dim']}; font-size: 13.5px; margin: 4px 0 20px 0; }}

    .stTextInput input, .stTextArea textarea, .stSelectbox > div > div {{
        background: {T['bg_card']} !important; border: 1px solid {T['border']} !important;
        color: {T['text']} !important; border-radius: 8px !important; font-size: 14px !important;
    }}
    .stTextInput input:focus, .stTextArea textarea:focus {{ border-color: {T['accent']} !important; box-shadow: 0 0 0 1px {T['accent']} !important; }}
    .stTextArea textarea {{ font-family: 'JetBrains Mono', monospace !important; font-size: 13px !important; }}

    .stButton button {{
        background: {T['accent']} !important; color: {T['btn_text']} !important; border: none !important;
        border-radius: 8px !important; font-weight: 700 !important; padding: 10px 22px !important;
        font-size: 14px !important; transition: all 0.15s ease !important;
    }}
    .stButton button:hover {{ filter: brightness(1.12); transform: translateY(-1px); }}
    .stDownloadButton button {{
        background: transparent !important; color: {T['accent']} !important;
        border: 1px solid {T['accent']} !important; border-radius: 8px !important; font-weight: 600 !important;
    }}

    .stTabs [data-baseweb="tab-list"] {{ gap: 4px; background: {T['bg_card']}; padding: 5px; border-radius: 10px; border: 1px solid {T['border']}; flex-wrap: wrap; }}
    .stTabs [data-baseweb="tab"] {{ background: transparent; border-radius: 7px; color: {T['text_dim']}; font-weight: 600; padding: 10px 16px; font-size: 13px; }}
    .stTabs [aria-selected="true"] {{ background: {T['accent']} !important; color: {T['btn_text']} !important; }}

    .output-card {{ background: {T['bg_card']}; border: 1px solid {T['border']}; border-radius: 10px; padding: 22px 24px; margin-top: 18px; color: {T['text']}; white-space: pre-wrap; font-size: 14px; line-height: 1.6; }}
    .output-card-label {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; color: {T['green']}; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }}

    .score-badge {{ display: inline-flex; align-items: center; gap: 8px; font-family: 'JetBrains Mono', monospace; font-size: 22px; font-weight: 700; padding: 8px 18px; border-radius: 8px; margin-bottom: 14px; }}
    .score-high {{ background: #3DD68C22; color: #3DD68C; border: 1px solid #3DD68C44; }}
    .score-mid {{ background: #FFB13C22; color: #FFB13C; border: 1px solid #FFB13C44; }}
    .score-low {{ background: #FF5C5C22; color: #FF5C5C; border: 1px solid #FF5C5C44; }}

    [data-testid="stSidebar"] {{ background: {T['bg_card']}; border-right: 1px solid {T['border']}; }}
    [data-testid="stSidebar"] .stMarkdown {{ color: {T['text']}; }}
    [data-testid="stChatMessage"] {{ background: {T['bg_card']} !important; border: 1px solid {T['border']} !important; border-radius: 10px !important; }}
    hr {{ border-color: {T['border']} !important; }}
    [data-testid="stDataFrame"] {{ border: 1px solid {T['border']}; border-radius: 8px; }}

    .chat-scroll {{ max-height: 480px; overflow-y: auto; padding: 8px 4px; margin-bottom: 12px; }}
    .bubble-user {{ background: {T['accent']}; color: {T['btn_text']}; padding: 10px 16px; border-radius: 18px 18px 4px 18px; max-width: 70%; font-size: 14px; line-height: 1.5; word-wrap: break-word; }}
    .bubble-ai {{ background: {T['bg_card']}; border: 1px solid {T['border']}; color: {T['text']}; padding: 10px 16px; border-radius: 18px 18px 18px 4px; max-width: 70%; font-size: 14px; line-height: 1.5; white-space: pre-wrap; word-wrap: break-word; }}

    .notice-box {{ background: {T['accent_dim']}; border: 1px solid {T['accent']}33; border-radius: 8px; padding: 10px 14px; font-size: 13px; color: {T['text_dim']}; margin-bottom: 12px; }}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────

def mask_key(key: str) -> str:
    """Return a masked display of an API key."""
    if not key or len(key) < 8:
        return "Not set"
    return f"{key[:4]}{'*' * 8}{key[-4:]}"


def call_llm(messages: list[dict], spinner_label: str = "Thinking...") -> str | None:
    """
    Call the Groq API with the given messages.
    Returns the response text, or None and shows an error on failure.
    """
    client = get_groq_client()
    if client is None:
        st.error(
            "GROQ_API_KEY is not set. Add it to your .env file and restart the app. "
            "Get a free key at https://console.groq.com"
        )
        return None
    try:
        with st.spinner(spinner_label):
            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=messages,
                timeout=API_TIMEOUT,
            )
        return response.choices[0].message.content
    except Exception as exc:
        err = str(exc)
        if "401" in err or "authentication" in err.lower():
            st.error("Authentication failed — check that your GROQ_API_KEY is correct.")
        elif "429" in err or "rate" in err.lower():
            st.error("Rate limit reached. Wait a moment and try again.")
        elif "model" in err.lower() and "not found" in err.lower():
            st.error(
                f"Model '{MODEL_ID}' was not found. "
                "Update GROQ_MODEL in your .env file to a supported model "
                "(see https://console.groq.com/docs/models)."
            )
        else:
            st.error(f"API request failed: {err}")
        return None


def safe_html_text(text: str) -> str:
    """Escape text for safe embedding inside HTML attributes/elements."""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


# ──────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"<div style=\"font-family:'JetBrains Mono',monospace;color:{T['accent']};font-size:13px;"
        f"font-weight:700;letter-spacing:1px;\">◆ AI CAREER SUITE</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    theme_choice = st.radio(
        "Theme", ["dark", "light"],
        index=0 if st.session_state.theme == "dark" else 1,
        horizontal=True
    )
    if theme_choice != st.session_state.theme:
        st.session_state.theme = theme_choice
        st.rerun()

    # API key status
    groq_key = get_setting("GROQ_API_KEY")
    if groq_key:
        st.markdown(
            f"<div class='notice-box'>✓ GROQ_API_KEY loaded<br>"
            f"<code style='font-size:11px'>{mask_key(groq_key)}</code></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='notice-box' style='border-color:#FF5C5C44;'>"
            "⚠ GROQ_API_KEY not set<br>"
            "Add it to .env and restart.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("**Stack**")
    st.markdown("`Python 3.12` `Streamlit` `Groq`")
    st.markdown(f"`{MODEL_ID}`")
    st.markdown("`pypdf` `python-docx` `pandas`")

    if st.session_state.score_history:
        st.markdown("---")
        avg = sum(s["score"] for s in st.session_state.score_history) / len(st.session_state.score_history)
        st.markdown("**Interview avg (this session)**")
        st.markdown(
            f"<span style='font-family:JetBrains Mono;font-size:24px;color:{T['accent']};"
            f"font-weight:700;'>{avg:.1f}/10</span>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("[GitHub →](https://github.com/kundurukalyan945-max/ai-agent-2026)")
    st.caption(f"Session started · {datetime.now().strftime('%H:%M')}")

    st.markdown("---")
    with st.expander("⚙️ Settings"):

        st.markdown("**Candidate profile**")
        st.caption("This profile is used by Resume Tailor and Crew. Update it to match your real background.")

        p = st.session_state.profile
        p["name"] = st.text_input("Name", value=p["name"], key="set_name")
        p["education"] = st.text_area("Education", value=p["education"], key="set_edu", height=70)
        p["skills"] = st.text_area("Skills", value=p["skills"], key="set_skills", height=70)
        p["project"] = st.text_area("Key project", value=p["project"], key="set_proj", height=70)
        p["target_role"] = st.text_input("Target role", value=p["target_role"], key="set_role")
        p["target_location"] = st.text_input("Target location", value=p["target_location"], key="set_loc")

        st.markdown("---")
        st.markdown("**Session data**")

        export_data = {
            "profile": st.session_state.profile,
            "chat_history_length": len(st.session_state.messages),
            "score_history": st.session_state.score_history,
            "exported_at": datetime.now().isoformat(),
        }
        st.download_button(
            "↓ Export session data (.json)",
            data=json.dumps(export_data, indent=2),
            file_name=f"career_suite_export_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            key="export_btn",
        )

        if st.button("Clear chat history", key="clear_chat_btn"):
            st.session_state.messages = []
            st.rerun()

        if st.button("Clear score history", key="clear_scores_btn"):
            st.session_state.score_history = []
            st.rerun()

        if st.button("Clear all session data", key="clear_all_btn"):
            for key, value in DEFAULTS.items():
                st.session_state[key] = value
            st.rerun()


# ──────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────
st.markdown(
    '<div class="suite-header">'
    '<span class="suite-mark">◆</span>'
    '<span class="suite-title">AI Career Suite</span>'
    '</div>'
    f'<div class="suite-sub">Career toolkit powered by {MODEL_ID} via Groq</div>',
    unsafe_allow_html=True,
)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Career Coach", "Resume Tailor", "Interview Prep", "Job Search", "Crew", "Career Agent"])


# ══════════════════════════════════════════════════════════
# TAB 1 — CAREER COACH
# ══════════════════════════════════════════════════════════
with tab1:
    st.markdown(
        '<div class="panel-head">'
        f'<span class="panel-tag">COACH</span>'
        '<span class="panel-title">Career Coach</span>'
        '</div>'
        '<div class="panel-desc">'
        'Ask career questions. Upload a PDF (resume or job posting) to discuss it. '
        'Chat history is kept for this session only — it resets when you close the app.'
        '</div>',
        unsafe_allow_html=True,
    )

    uploaded_pdf = st.file_uploader(
        "Upload a PDF (resume, job posting, anything)",
        type=["pdf"],
        key="coach_pdf",
    )
    pdf_text = ""
    if uploaded_pdf:
        try:
            from pypdf import PdfReader
            reader = PdfReader(uploaded_pdf)
            pdf_text = "\n".join(page.extract_text() or "" for page in reader.pages)
            pdf_text = pdf_text[:MAX_PDF_CHARS]
            st.success(f"📄 {uploaded_pdf.name} — {len(reader.pages)} page(s) loaded. Ask about it below.")
        except ImportError:
            st.error("pypdf is not installed. Run: pip install pypdf")
        except Exception as exc:
            st.error(f"Could not read PDF: {exc}")

    # Render chat history — content is escaped before inserting into HTML
    st.markdown('<div class="chat-scroll">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        bubble_class = "bubble-user" if msg["role"] == "user" else "bubble-ai"
        align = "flex-end" if msg["role"] == "user" else "flex-start"
        safe_content = safe_html_text(str(msg["content"]))
        st.markdown(
            f'<div style="display:flex;justify-content:{align};margin:6px 0;">'
            f'<div class="{bubble_class}">{safe_content}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    if prompt := st.chat_input("Ask your career coach anything..."):
        if len(prompt) > MAX_INPUT_CHARS:
            st.warning(f"Message too long — truncated to {MAX_INPUT_CHARS} characters.")
            prompt = prompt[:MAX_INPUT_CHARS]

        full_prompt = prompt
        if pdf_text:
            full_prompt = (
                f"[PDF context from '{uploaded_pdf.name}']:\n{pdf_text}\n\n"
                f"[Question]: {prompt}"
            )

        st.session_state.messages.append({"role": "user", "content": prompt})

        system_msg = (
            "You are an AI career coach helping a job seeker. "
            "Give practical, honest, actionable advice. "
            "If PDF context is provided, use it to answer the question. "
            "Do not invent job offers, certifications, or employment history."
        )
        api_messages = [{"role": "system", "content": system_msg}]
        for i, m in enumerate(st.session_state.messages):
            if i == len(st.session_state.messages) - 1 and m["role"] == "user":
                api_messages.append({"role": "user", "content": full_prompt})
            else:
                api_messages.append({"role": m["role"], "content": m["content"]})

        reply = call_llm(api_messages, "Thinking...")
        if reply:
            st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()


# ══════════════════════════════════════════════════════════
# TAB 2 — RESUME TAILOR
# ══════════════════════════════════════════════════════════
with tab2:
    st.markdown(
        '<div class="panel-head">'
        f'<span class="panel-tag">RESUME</span>'
        '<span class="panel-title">Resume Tailor</span>'
        '</div>'
        '<div class="panel-desc">'
        'Paste a job description to get ATS keywords, rewritten bullets, and a summary. '
        'All suggestions are based on your profile — verify them before using. '
        '<strong>AI output is a starting point, not a finished resume.</strong>'
        '</div>',
        unsafe_allow_html=True,
    )

    p = st.session_state.profile
    if p["name"] == "Your Name":
        st.info("Update your candidate profile in Settings (sidebar) before tailoring.")

    job_desc = st.text_area(
        "Job description",
        height=160,
        label_visibility="collapsed",
        placeholder="Paste the full job description here...",
    )

    if st.button("Tailor my resume", key="tailor_btn"):
        if not job_desc.strip():
            st.warning("Paste a job description first.")
        elif len(job_desc) > MAX_INPUT_CHARS:
            st.warning(f"Job description too long — truncated to {MAX_INPUT_CHARS} characters.")
            job_desc = job_desc[:MAX_INPUT_CHARS]
        else:
            messages = [
                {"role": "system", "content": (
                    "You are an expert resume writer. "
                    "Suggest improvements based only on the candidate's actual background. "
                    "Do not fabricate experience, certifications, metrics, or employers."
                )},
                {"role": "user", "content": (
                    f"Candidate background:\n"
                    f"Name: {p['name']}\n"
                    f"Education: {p['education']}\n"
                    f"Skills: {p['skills']}\n"
                    f"Project: {p['project']}\n"
                    f"Target role: {p['target_role']} in {p['target_location']}\n\n"
                    f"Job description:\n{job_desc}\n\n"
                    "Provide:\n"
                    "1. Top 5 ATS keywords from the job description to include\n"
                    "2. Three rewritten project or experience bullet points that match this role "
                    "(based only on the project and skills listed above)\n"
                    "3. A 3-line professional summary for this specific role\n\n"
                    "Note: these are suggestions only. The candidate must verify and edit before using."
                )},
            ]
            result = call_llm(messages, "Analysing job description...")
            if result:
                st.session_state.last_resume = result

    if st.session_state.last_resume:
        st.markdown(
            f'<div class="output-card">'
            f'<div class="output-card-label">● suggestions ready — review before using</div>'
            f'{safe_html_text(st.session_state.last_resume)}'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.caption("⚠ ATS keyword suggestions do not guarantee an ATS score, shortlist, or interview.")

        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                "↓ Download as .txt",
                data=st.session_state.last_resume,
                file_name=f"resume_suggestions_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
            )
        with dl2:
            try:
                from docx import Document
                doc = Document()
                doc.add_heading("Resume Suggestions", level=1)
                doc.add_paragraph(
                    "These are AI-generated suggestions. Review and edit before using in a real application."
                )
                doc.add_paragraph("")
                for line in st.session_state.last_resume.split("\n"):
                    if line.strip():
                        doc.add_paragraph(line)
                buf = io.BytesIO()
                doc.save(buf)
                buf.seek(0)
                st.download_button(
                    "↓ Download as .docx",
                    data=buf,
                    file_name=f"resume_suggestions_{datetime.now().strftime('%Y%m%d')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            except ImportError:
                st.caption("Install python-docx for Word download: pip install python-docx")


# ══════════════════════════════════════════════════════════
# TAB 3 — INTERVIEW PREP
# ══════════════════════════════════════════════════════════
with tab3:
    st.markdown(
        '<div class="panel-head">'
        f'<span class="panel-tag">INTERVIEW</span>'
        '<span class="panel-title">Interview Prep</span>'
        '</div>'
        '<div class="panel-desc">'
        'Practise answering common AI/ML interview questions and receive structured feedback. '
        'Scores are tracked for this session. '
        'AI feedback is a practice aid — it does not predict actual interview outcomes.'
        '</div>',
        unsafe_allow_html=True,
    )

    questions = [
        "Tell me about yourself and why you want to work in AI/ML.",
        "What is machine learning and how does it differ from traditional programming?",
        "What is the difference between supervised and unsupervised learning?",
        "Describe a project you have built and the technical challenges you faced.",
        "What is overfitting and how do you prevent it?",
        "Explain the bias-variance trade-off.",
        "How does a neural network learn?",
    ]

    question = st.selectbox("Select a question", questions)
    answer = st.text_area(
        "Your answer",
        height=140,
        label_visibility="collapsed",
        placeholder="Type your answer here...",
    )

    if st.button("Score my answer", key="score_btn"):
        if not answer.strip():
            st.warning("Type your answer first.")
        elif len(answer) > MAX_INPUT_CHARS:
            st.warning(f"Answer too long — truncated to {MAX_INPUT_CHARS} characters.")
            answer = answer[:MAX_INPUT_CHARS]
        else:
            messages = [
                {"role": "system", "content": (
                    "You are a technical interviewer. "
                    "Give a numeric score out of 10 and structured feedback. "
                    "Be direct and constructive."
                )},
                {"role": "user", "content": (
                    f"Question: {question}\n"
                    f"Answer: {answer}\n\n"
                    "Reply in exactly this format:\n"
                    "SCORE: X/10\n"
                    "STRENGTHS: (one sentence)\n"
                    "IMPROVE: (one sentence)\n"
                    "EXAMPLE ANSWER: (2–3 sentences)"
                )},
            ]
            feedback = call_llm(messages, "Evaluating answer...")
            if feedback:
                lines = feedback.split("\n")
                score_line = next((l for l in lines if l.startswith("SCORE:")), None)
                score_val = 0
                if score_line:
                    try:
                        score_val = int(score_line.split("/")[0].replace("SCORE:", "").strip())
                    except ValueError:
                        score_val = 0

                css_class = (
                    "score-high" if score_val >= 7
                    else "score-mid" if score_val >= 5
                    else "score-low"
                )

                # Safe: score_line contains "SCORE: X/10" — no user HTML
                display_score = score_line.strip() if score_line else f"SCORE: {score_val}/10"
                st.markdown(
                    f'<div class="score-badge {css_class}">{safe_html_text(display_score)}</div>',
                    unsafe_allow_html=True,
                )

                feedback_body = "\n".join(l for l in lines if not l.startswith("SCORE:"))
                st.markdown(
                    f'<div class="output-card">{safe_html_text(feedback_body)}</div>',
                    unsafe_allow_html=True,
                )

                if score_val > 0:
                    st.session_state.score_history.append({
                        "time": datetime.now().strftime("%H:%M"),
                        "question": question[:40] + "…",
                        "score": score_val,
                    })

    if st.session_state.score_history:
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        st.markdown(
            '<div class="panel-head">'
            f'<span class="panel-tag">PROGRESS</span>'
            '<span class="panel-title" style="font-size:16px;">Score History (this session)</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        df = pd.DataFrame(st.session_state.score_history)
        st.line_chart(df.set_index("time")["score"], height=200)
        st.dataframe(df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════
# TAB 4 — JOB SEARCH
# ══════════════════════════════════════════════════════════
with tab4:
    st.markdown(
        '<div class="panel-head">'
        f'<span class="panel-tag">JOBS</span>'
        '<span class="panel-title">Job Search</span>'
        '</div>'
        '<div class="panel-desc">'
        'Search for live job postings via Indeed. Results depend on what is available at the time of search. '
        'Listings may not be current — always verify on the original posting before applying.'
        '</div>',
        unsafe_allow_html=True,
    )

    jc1, jc2 = st.columns([3, 1])
    with jc1:
        search_term = st.text_input(
            "Search term",
            value="AI ML Python developer",
            label_visibility="collapsed",
        )
    with jc2:
        search_btn = st.button("Search jobs", key="job_search_btn")

    if search_btn:
        if not search_term.strip():
            st.warning("Enter a search term.")
        else:
            with st.spinner("Searching Indeed (this can take up to 30 seconds)..."):
                try:
                    from jobspy import scrape_jobs
                    jobs = scrape_jobs(
                        site_name=["indeed"],
                        search_term=search_term,
                        location="Bengaluru, India",
                        results_wanted=15,
                        hours_old=72,
                        country_indeed="India",
                    )
                    if jobs is not None and not jobs.empty:
                        cols = [c for c in ["title", "company", "location", "date_posted", "job_url"] if c in jobs.columns]
                        st.session_state.job_results = jobs[cols].copy()
                    else:
                        st.session_state.job_results = None
                        st.info("No jobs found for that search term. Try different keywords.")
                except ImportError:
                    st.error("python-jobspy is not installed. Run: pip install python-jobspy")
                except Exception as exc:
                    st.error(f"Search failed: {exc}")
                    st.session_state.job_results = None

    if st.session_state.job_results is not None:
        count = len(st.session_state.job_results)
        retrieved_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.markdown(
            f'<div class="output-card-label" style="margin-top:18px;">'
            f'● {count} results from Indeed · retrieved {retrieved_at}'
            f'</div>',
            unsafe_allow_html=True,
        )
        col_config = {}
        if "job_url" in st.session_state.job_results.columns:
            col_config["job_url"] = st.column_config.LinkColumn("Apply link")
        st.dataframe(
            st.session_state.job_results,
            use_container_width=True,
            hide_index=True,
            column_config=col_config,
        )
        csv = st.session_state.job_results.to_csv(index=False).encode("utf-8")
        st.download_button(
            "↓ Download as CSV",
            data=csv,
            file_name=f"jobs_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )
        st.caption(
            "Source: Indeed India. Results depend on current availability and may include expired listings. "
            "Always check the original posting before applying."
        )


# ══════════════════════════════════════════════════════════
# TAB 5 — CREW (sequential AI workflow)
# ══════════════════════════════════════════════════════════
with tab5:
    st.markdown(
        '<div class="panel-head">'
        f'<span class="panel-tag">CREW</span>'
        '<span class="panel-title">Company Research Workflow</span>'
        '</div>'
        '<div class="panel-desc">'
        'Three sequential AI steps prepare you for a specific company and role: '
        'research → resume suggestions → interview prep. '
        'This is a sequential workflow using your candidate profile — not an autonomous agent system. '
        'Each step feeds its output into the next.'
        '</div>',
        unsafe_allow_html=True,
    )

    p = st.session_state.profile
    if p["name"] == "Your Name":
        st.info("Update your candidate profile in Settings before running the workflow.")

    cc1, cc2 = st.columns(2)
    with cc1:
        crew_company = st.text_input("Company", placeholder="e.g. Google")
    with cc2:
        crew_role = st.text_input("Role", placeholder="e.g. AI Engineer")

    if st.button("Run workflow", key="crew_btn"):
        if not crew_company.strip() or not crew_role.strip():
            st.warning("Enter both a company name and a role.")
        else:
            progress = st.progress(0, text="Step 1 of 3 — Researching company...")

            research = call_llm(
                messages=[
                    {"role": "system", "content": "You are a job market researcher. Give factual, practical information."},
                    {"role": "user", "content": (
                        f"Research {crew_company} for someone applying for {crew_role}. "
                        "Cover: what the company does, their tech stack, culture, "
                        f"what they look for in {crew_role} candidates, and 5 important resume keywords."
                    )},
                ],
                spinner_label="Step 1 — Researching company...",
            )

            if research is None:
                st.error("Step 1 failed. Check your API key and try again.")
                st.stop()

            progress.progress(33, text="Step 2 of 3 — Tailoring resume...")

            profile_summary = (
                f"Name: {p['name']}\n"
                f"Education: {p['education']}\n"
                f"Skills: {p['skills']}\n"
                f"Project: {p['project']}\n"
                f"Target role: {p['target_role']}"
            )
            resume = call_llm(
                messages=[
                    {"role": "system", "content": (
                        "You are a resume specialist. "
                        "Tailor content based only on the candidate's actual background. "
                        "Do not invent experience, metrics, or qualifications."
                    )},
                    {"role": "user", "content": (
                        f"Company research:\n{research}\n\n"
                        f"Candidate profile:\n{profile_summary}\n\n"
                        f"Tailor this profile for {crew_role} at {crew_company}. "
                        "Provide: a 3-line professional summary, 4 experience/project bullet points, "
                        "and 6 ATS keywords. Base everything only on the profile above."
                    )},
                ],
                spinner_label="Step 2 — Tailoring resume...",
            )

            if resume is None:
                st.error("Step 2 failed.")
                st.stop()

            progress.progress(66, text="Step 3 of 3 — Preparing interview questions...")

            interview = call_llm(
                messages=[
                    {"role": "system", "content": "You are a technical interview coach."},
                    {"role": "user", "content": (
                        f"Company research:\n{research}\n\n"
                        f"Candidate profile:\n{profile_summary}\n\n"
                        f"Prepare this candidate for a {crew_role} interview at {crew_company}:\n"
                        "1. Five likely technical questions with suggested answers\n"
                        "2. Three behavioural questions with STAR-format answer outlines\n"
                        "3. Two smart questions to ask the interviewer\n"
                        "Base answers on the candidate profile above."
                    )},
                ],
                spinner_label="Step 3 — Preparing interview questions...",
            )

            if interview is None:
                st.error("Step 3 failed.")
                st.stop()

            progress.progress(100, text="Complete.")

            for label, content in [
                ("step 1 — company research", research),
                ("step 2 — resume suggestions", resume),
                ("step 3 — interview preparation", interview),
            ]:
                st.markdown(
                    f'<div class="output-card">'
                    f'<div class="output-card-label">● {label}</div>'
                    f'{safe_html_text(content)}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            full_report = (
                f"WORKFLOW REPORT: {crew_role} at {crew_company}\n"
                f"Generated: {datetime.now().isoformat()}\n\n"
                f"=== STEP 1: COMPANY RESEARCH ===\n{research}\n\n"
                f"=== STEP 2: RESUME SUGGESTIONS ===\n{resume}\n\n"
                f"=== STEP 3: INTERVIEW PREPARATION ===\n{interview}\n"
            )
            st.download_button(
                "↓ Download full report (.txt)",
                data=full_report,
                file_name=f"crew_{crew_company.replace(' ', '_')}_{crew_role.replace(' ', '_')}.txt",
                mime="text/plain",
            )


# ══════════════════════════════════════════════════════════
# TAB 6 — PERSISTENT CAREER AGENT
# ══════════════════════════════════════════════════════════
    with tab6:
        private_password = get_setting("APP_ACCESS_PASSWORD")
        if not private_password:
            st.error("Career Agent is locked.")
            st.warning(
                "This is a public Streamlit app. To unlock the private workspace, set APP_ACCESS_PASSWORD "
                "in Streamlit Community Cloud → App settings → Secrets. Do not put the password in GitHub."
            )
        else:
            if not st.session_state.get("career_agent_authenticated", False):
                entered_password = st.text_input(
                    "Private Career Agent password",
                    type="password",
                    key="career_agent_password_input",
                )
                if st.button("Unlock Career Agent", key="career_agent_unlock"):
                    if hmac.compare_digest(entered_password, private_password):
                        st.session_state["career_agent_authenticated"] = True
                        st.rerun()
                    else:
                        st.error("Incorrect password.")
            if st.session_state.get("career_agent_authenticated", False):
        st.markdown(
            '<div class="panel-head">'
            f'<span class="panel-tag">CAREER OS</span>'
            '<span class="panel-title">Personal Career Agent</span>'
            '</div>'
            '<div class="panel-desc">'
            'Persistent job tracking, transparent matching, application-pack preparation, '
            'referral research and an auditable approval queue. External actions are not executed by this release.'
            '</div>',
            unsafe_allow_html=True,
        )

        legacy_profile = st.session_state.profile
        profile_defaults = {
            "name": (
                "Kalyan Kunduru" if legacy_profile.get("name") in (None, "", "Your Name")
                else legacy_profile.get("name")
            ),
            "education": (
                "B.Tech, Computer Science & Engineering (AI/ML), Sri Venkateswara College of Engineering, Tirupati; graduated May 2026; CGPA 7.3/10"
                if legacy_profile.get("education", "").startswith("Degree, University")
                else legacy_profile.get("education", "")
            ),
            "skills": (
                "Python, SQL, Pandas, NumPy, Matplotlib, scikit-learn, TensorFlow, YOLOv8, OpenCV, Streamlit, Jupyter Notebook, Git, GitHub, REST APIs, Vercel, LangChain, RAG, LLaMA 3.3, Groq API, prompt engineering"
                if legacy_profile.get("skills", "").startswith("List your skills")
                else legacy_profile.get("skills", "")
            ),
            "projects": (
                "AI Career Suite: five-agent application with job scraping, resume tailoring, interview coaching, PDF reading and orchestration; YOLOv8 object detection with OpenCV, Streamlit and offline text-to-speech; reported 93–95% project-test accuracy and sub-200 ms inference; presented at ACMETECH-2K26 (March 2026)."
                if legacy_profile.get("project", "").startswith("Your key project")
                else legacy_profile.get("project", "")
            ),
            "experience": "Entry-level candidate; AI & Machine Learning Intern — SmartBridge / APSCHE / Google for Developers (Oct 2025–Mar 2026, 240-hour programme); JPMorgan Chase & Co. and Deloitte virtual job simulations via Forage.",
            "years_experience": 0,
            "target_roles": [
                "AI/ML Engineer", "AI Engineer", "Generative AI Engineer", "Python Developer",
                "Junior Data Scientist", "ML Analyst", "Data Analyst", "Analytics Associate",
                "Reporting Analyst", "Machine Learning Engineer", "LLM Engineer",
                "AI Application Developer", "Python Backend Developer"
            ],
            "target_locations": ["Bengaluru", "Hyderabad"],
            "salary_min_lpa": 4,
            "salary_max_lpa": 8,
        }
        try:
            saved_profile = get_profile()
            if not saved_profile:
                saved_profile = profile_defaults
                save_profile(saved_profile)
        except Exception as exc:
            st.error(f"Career database could not be opened: {exc}")
            saved_profile = profile_defaults

        sub_overview, sub_jobs, sub_network, sub_review, sub_profile = st.tabs(
            ["Overview", "Job Pipeline", "Network & Referrals", "Approval Queue", "Candidate Profile"]
        )

        with sub_overview:
            all_jobs = list_jobs()
            pending_items = list_approvals("pending")
            approved_items = list_approvals("approved")
            c1, c2, c3 = st.columns(3)
            c1.metric("Saved jobs", len(all_jobs))
            c2.metric("Awaiting review", len(pending_items))
            c3.metric("Approved drafts", len(approved_items))
            st.info(
                "Safety boundary: this app can research, score, draft and record your approval. "
                "It does not submit applications or send recruiter messages. Approval is not execution."
            )
            st.markdown("**Daily Job Radar integration**")
            st.write(
                "Your existing 9:00 AM Daily Fresher Job Radar remains active. "
                "Use Job Pipeline → Import current Job Search results for one-click intake from the existing scraper, "
                "or add a verified job URL manually. The scheduled radar remains the broader daily discovery source."
            )
            if os.getenv("CAREER_DB_PATH"):
                st.caption(f"Database path configured: {os.getenv('CAREER_DB_PATH')}")
            else:
                st.warning(
                    "Storage note: SQLite currently saves to the app filesystem. "
                    "For Streamlit Cloud persistence across rebuilds/restarts, configure CAREER_DB_PATH "
                    "to a durable mounted volume or migrate this adapter to hosted PostgreSQL/Supabase."
                )

        with sub_jobs:
            st.markdown("### Add jobs to your pipeline")
            radar_csv = st.file_uploader(
                "Import a CSV exported from your job tracker / Daily Job Radar",
                type=["csv"],
                key="career_radar_csv",
                help="Expected columns include title, company, location and job_url/url; description and date_posted are optional."
            )
            radar_csv_text = st.text_area(
                "Or paste the CSV block from your 9 AM Daily Job Radar",
                height=100,
                key="career_radar_csv_text",
                help="Paste the CSV header and rows only (without Markdown code fences)."
            )
            if st.button("Import pasted Daily Job Radar CSV", key="career_import_csv_text"):
                if not radar_csv_text.strip():
                    st.warning("Paste CSV rows first.")
                else:
                    try:
                        pasted_frame = pd.read_csv(io.StringIO(radar_csv_text)).fillna("")
                        imported_text = 0
                        for _, pasted_row in pasted_frame.iterrows():
                            row_dict = pasted_row.to_dict()
                            add_job({
                                "title": row_dict.get("title") or row_dict.get("job_title", ""),
                                "company": row_dict.get("company") or row_dict.get("employer", ""),
                                "location": row_dict.get("location", ""),
                                "work_mode": row_dict.get("work_mode", ""),
                                "url": row_dict.get("job_url") or row_dict.get("url", ""),
                                "description": row_dict.get("description") or row_dict.get("job_description", ""),
                                "date_posted": row_dict.get("date_posted", ""),
                                "source": row_dict.get("source") or "Daily Job Radar",
                            })
                            imported_text += 1
                        st.success(f"Imported/refreshed {imported_text} pasted CSV rows.")
                    except Exception as exc:
                        st.error(f"Pasted CSV could not be imported: {exc}")
            if radar_csv is not None:
                if st.button("Import uploaded job CSV", key="career_import_csv"):
                    try:
                        radar_frame = pd.read_csv(radar_csv).fillna("")
                        imported_csv = 0
                        for _, csv_row in radar_frame.iterrows():
                            row_dict = csv_row.to_dict()
                            add_job({
                                "title": row_dict.get("title") or row_dict.get("job_title", ""),
                                "company": row_dict.get("company") or row_dict.get("employer", ""),
                                "location": row_dict.get("location", ""),
                                "url": row_dict.get("job_url") or row_dict.get("url", ""),
                                "description": row_dict.get("description") or row_dict.get("job_description", ""),
                                "date_posted": row_dict.get("date_posted", ""),
                                "source": row_dict.get("source") or "Imported CSV",
                            })
                            imported_csv += 1
                        st.success(f"Imported/refreshed {imported_csv} CSV rows. URL duplicates are deduplicated.")
                    except Exception as exc:
                        st.error(f"CSV import failed: {exc}")
            current_results = st.session_state.get("job_results")
            if current_results is not None and hasattr(current_results, "empty") and not current_results.empty:
                if st.button("Import current Job Search results", key="career_import_job_results"):
                    imported = 0
                    for _, row in current_results.iterrows():
                        try:
                            add_job({
                                "title": row.get("title", ""),
                                "company": row.get("company", ""),
                                "location": row.get("location", ""),
                                "url": row.get("job_url", ""),
                                "date_posted": row.get("date_posted", ""),
                                "source": "AI Career Suite Job Search",
                            })
                            imported += 1
                        except Exception:
                            continue
                    st.success(f"Imported/refreshed {imported} job records. URL duplicates are updated, not duplicated.")

            with st.form("career_add_job_form", clear_on_submit=True):
                left, right = st.columns(2)
                with left:
                    manual_title = st.text_input("Job title", placeholder="Junior Python Developer")
                    manual_company = st.text_input("Company", placeholder="Company name")
                    manual_location = st.text_input("Location", placeholder="Hyderabad / Bengaluru")
                with right:
                    manual_url = st.text_input("Official job URL", placeholder="https://company.com/careers/job-id")
                    manual_mode = st.selectbox("Work mode", ["Not specified", "On-site", "Hybrid", "Remote"])
                    manual_source = st.text_input("Source", value="Manual / official careers page")
                manual_description = st.text_area(
                    "Job description / requirements",
                    height=150,
                    placeholder="Paste the job description. Do not include passwords or private account data."
                )
                submitted_job = st.form_submit_button("Save job to pipeline")
            if submitted_job:
                if not manual_title.strip() or not manual_company.strip():
                    st.warning("Enter at least a job title and company.")
                else:
                    try:
                        add_job({
                            "title": manual_title, "company": manual_company,
                            "location": manual_location, "url": manual_url,
                            "work_mode": "" if manual_mode == "Not specified" else manual_mode,
                            "source": manual_source, "description": manual_description,
                        })
                        st.success("Job saved. Duplicate URLs are automatically refreshed.")
                    except Exception as exc:
                        st.error(f"Could not save job: {exc}")

            jobs_for_review = list_jobs()
            st.markdown("### Match and prepare")
            if not jobs_for_review:
                st.info("No saved jobs yet. Import Job Search results or add a role above.")
            else:
                profile_for_match = get_profile() or saved_profile
                scored = []
                for job_row in jobs_for_review:
                    payload = job_row.get("payload", {})
                    fit = score_job(payload, profile_for_match)
                    scored.append({
                        "Fit": fit["score"],
                        "Role": job_row["title"],
                        "Company": job_row["company"],
                        "Location": job_row["location"],
                        "Skills matched": ", ".join(fit["matched_skills"]),
                        "Skill gaps": ", ".join(fit["skill_gaps"]),
                        "Job ID": job_row["job_id"],
                    })
                scored.sort(key=lambda item: item["Fit"], reverse=True)
                display_rows = [{k: v for k, v in row.items() if k != "Job ID"} for row in scored]
                st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)
                st.caption("Fit score is a transparent keyword/location heuristic, not an ATS score or probability of selection.")

                for row in scored[:20]:
                    job_row = next(j for j in jobs_for_review if j["job_id"] == row["Job ID"])
                    payload = job_row.get("payload", {})
                    fit = score_job(payload, profile_for_match)
                    with st.expander(f"{fit['score']}/100 · {job_row['title']} — {job_row['company']}"):
                        st.write(job_row["location"] or "Location not specified")
                        if job_row.get("url"):
                            st.markdown(f"[Open original job posting]({job_row['url']})")
                        st.write("**Match reasons**")
                        for reason in fit["reasons"]:
                            st.write(f"- {reason}")
                        if fit["matched_skills"]:
                            st.write("**Matched skills:** " + ", ".join(fit["matched_skills"]))
                        if fit["skill_gaps"]:
                            st.write("**Potential gaps:** " + ", ".join(fit["skill_gaps"]))
                        st.caption(fit["note"])
                        if st.button("Prepare application pack", key=f"career_prepare_{job_row['job_id']}"):
                            profile_text = json.dumps(profile_for_match, ensure_ascii=False, indent=2)
                            job_text = json.dumps(payload, ensure_ascii=False, indent=2)[:9000]
                            packet = call_llm(
                                [
                                    {
                                        "role": "system",
                                        "content": (
                                            "You are a careful career application preparation agent. "
                                            "Use only facts present in the candidate profile. Never invent employers, "
                                            "degrees, dates, metrics, certifications, skills or achievements. "
                                            "Mark missing facts as [CANDIDATE TO VERIFY]. Do not claim an application "
                                            "was submitted. Produce a concise Markdown application preparation pack."
                                        ),
                                    },
                                    {
                                        "role": "user",
                                        "content": (
                                            f"CANDIDATE PROFILE (source of truth):\n{profile_text}\n\n"
                                            f"JOB POSTING:\n{job_text}\n\n"
                                            "Prepare: (1) fit summary and evidence, (2) explicit gaps, "
                                            "(3) tailored professional summary, (4) truthful project/experience bullets, "
                                            "(5) ATS keyword suggestions with no keyword stuffing, "
                                            "(6) short cover-letter draft, (7) five interview topics, "
                                            "(8) candidate verification checklist."
                                        ),
                                    },
                                ],
                                "Preparing a job-specific application pack...",
                            )
                            if packet:
                                approval_id = create_approval(
                                    "application_packet",
                                    f"Application pack — {job_row['title']} at {job_row['company']}",
                                    {
                                        "job_id": job_row["job_id"],
                                        "job": payload,
                                        "candidate_profile": profile_for_match,
                                        "draft": packet,
                                        "external_action": "not_executed",
                                    },
                                    company=job_row["company"],
                                    role=job_row["title"],
                                )
                                st.success(f"Draft saved to Approval Queue (reference: {approval_id[:8]}). Nothing was submitted.")
                                st.markdown(packet)
                                st.download_button(
                                    "Download preparation pack",
                                    data=packet,
                                    file_name=f"application_pack_{job_row['company'].replace(' ', '_')}.md",
                                    mime="text/markdown",
                                    key=f"career_pack_dl_{job_row['job_id']}",
                                )


        with sub_network:
            st.markdown("### Happenstance network research")
            hs = connection_status()
            st.markdown(
                "Search your connected professional network for recruiters, hiring managers, engineers and warm introduction paths. "
                "Happenstance is a people/network search service, not a job board."
            )
            st.markdown(
                "[Happenstance](https://happenstance.ai/) · "
                "[Official API documentation](https://developer.happenstance.ai/api-reference/introduction)"
            )
            profile_net = get_profile() or saved_profile
            target_roles_net = profile_net.get("target_roles", ["AI Engineer"])
            target_locations_net = profile_net.get("target_locations", ["Bengaluru", "Hyderabad"])
            suggested_prompt = referral_search_prompt(
                "companies hiring entry-level AI and software candidates",
                ", ".join(target_roles_net[:3]),
                ", ".join(target_locations_net),
            )

            if hs["api_ready"]:
                st.success("Happenstance API key detected in secure app configuration.")
                st.caption("Upload your LinkedIn connections to Happenstance before searching your personal network.")
                try:
                    usage = get_usage()
                    balance = usage.get("balance_credits")
                    if balance is not None:
                        st.metric("Happenstance credit balance", balance)
                except HappenstanceError as exc:
                    st.warning(str(exc))

                st.caption(
                    "Happenstance charges 2 credits per completed search. Checking status/results does not create another search."
                )
                search_query = st.text_area(
                    "Network search query",
                    value=suggested_prompt,
                    height=120,
                    key="hs_api_query",
                )
                hc1, hc2 = st.columns(2)
                with hc1:
                    include_my_connections = st.checkbox(
                        "Search my direct connections", value=True, key="hs_my_connections"
                    )
                with hc2:
                    include_friends_connections = st.checkbox(
                        "Also search friends' connections", value=False, key="hs_friend_connections"
                    )
                confirm_cost = st.checkbox(
                    "I understand this search consumes 2 Happenstance credits.",
                    value=False,
                    key="hs_cost_confirm",
                )
                if st.button(
                    "Start Happenstance search (2 credits)",
                    key="hs_start_search",
                    disabled=(not confirm_cost or not search_query.strip()),
                ):
                    try:
                        created = create_network_search(
                            search_query,
                            include_my_connections=include_my_connections,
                            include_friends_connections=include_friends_connections,
                        )
                        st.session_state["hs_active_search_id"] = created["id"]
                        st.session_state["hs_active_search_url"] = created["url"]
                        st.session_state["hs_active_search_status"] = "RUNNING"
                        st.session_state["hs_people_results"] = []
                        st.success("Search created. Results may take time to finish.")
                    except (HappenstanceError, ValueError) as exc:
                        st.error(str(exc))

                active_id = st.session_state.get("hs_active_search_id")
                active_url = st.session_state.get("hs_active_search_url")
                if active_id:
                    if active_url:
                        st.markdown("[Open this search in Happenstance](" + str(active_url) + ")")
                    status_now = st.session_state.get("hs_active_search_status", "RUNNING")
                    st.caption("Active search: " + str(active_id) + " · Status: " + str(status_now))
                    if st.button("Refresh search status and results", key="hs_refresh_search"):
                        try:
                            search_data = get_network_search(active_id)
                            status_now = str(search_data.get("status", "UNKNOWN")).upper()
                            st.session_state["hs_active_search_status"] = status_now
                            if status_now == "COMPLETED":
                                st.session_state["hs_people_results"] = flatten_search_results(search_data)
                                st.success(
                                    "Search completed. "
                                    + str(len(st.session_state["hs_people_results"]))
                                    + " people returned."
                                )
                            elif status_now == "FAILED":
                                st.error("Happenstance reports that this search failed. Review the query before starting another.")
                            else:
                                st.info("Search is still " + status_now + ". Refresh again shortly.")
                        except HappenstanceError as exc:
                            st.error(str(exc))

                    people = st.session_state.get("hs_people_results", [])
                    if people:
                        people_df = pd.DataFrame(people)
                        display_cols = [
                            col for col in
                            ["name", "title", "company", "relevance_score", "mutuals", "linkedin_url", "happenstance_url"]
                            if col in people_df.columns
                        ]
                        st.dataframe(people_df[display_cols], use_container_width=True, hide_index=True)
                        labels = [
                            str(person["name"]) + " — " + str(person.get("title") or "Role not listed")
                            + " @ " + str(person.get("company") or "Company not listed")
                            for person in people
                        ]
                        label_to_person = dict(zip(labels, people))
                        selected = st.multiselect(
                            "Select people for whom to prepare messages",
                            options=labels,
                            key="hs_selected_people",
                        )
                        if selected and st.button("Prepare message for selected people", key="hs_make_message"):
                            selected_people = [label_to_person[label] for label in selected]
                            profile_text = json.dumps(profile_net, ensure_ascii=False, indent=2)
                            findings_text = json.dumps(selected_people, ensure_ascii=False, indent=2)
                            draft = call_llm(
                                [
                                    {
                                        "role": "system",
                                        "content": (
                                            "Write concise, respectful professional networking messages. "
                                            "Use only supplied person details and the candidate profile. Never invent a prior "
                                            "relationship, shared history, current vacancy or promised referral. "
                                            "Prepare one message per selected person and mark uncertain facts for verification."
                                        ),
                                    },
                                    {
                                        "role": "user",
                                        "content": (
                                            "Candidate profile:\n" + profile_text
                                            + "\n\nSelected Happenstance results:\n" + findings_text
                                            + "\n\nWrite a short message asking for relevant career advice or referral guidance. "
                                            "Only mention a mutual connection when the search result lists one."
                                        ),
                                    },
                                ],
                                "Preparing messages for selected network connections...",
                            )
                            if draft:
                                review_id = create_approval(
                                    "network_message",
                                    "Review Happenstance networking messages",
                                    {
                                        "selected_people": selected_people,
                                        "draft": draft,
                                        "external_action": "not_executed",
                                    },
                                )
                                st.success(
                                    "Draft added to Approval Queue (" + review_id[:8] + "). No message has been sent."
                                )
                                st.markdown(draft)
            else:
                st.warning(
                    "Direct Happenstance API search is not configured in this app. "
                    "Add HAPPENSTANCE_API_KEY through Streamlit app Settings → Secrets or the server environment. "
                    "Never paste the API key into a chat box or commit it to GitHub."
                )
                st.markdown("**Suggested prompt for Happenstance's website or ChatGPT connection**")
                st.text_area(
                    "Copy this prompt into Happenstance",
                    value=suggested_prompt,
                    height=120,
                    key="hs_manual_prompt",
                )
                st.markdown("[Official ChatGPT integration guide](https://developer.happenstance.ai/mcp/chatgpt)")

            st.caption(
                "Search results stay in this app session. Selected people and the generated draft are stored in the "
                "approval queue for review. This app does not send messages or contact anyone."
            )

        with sub_review:
            st.markdown("### Human approval queue")
            st.info(
                "Approve/reject records your decision and preserves an audit trail. "
                "It does not send an email, LinkedIn message, or job application. "
                "This release has no external-action executor connected."
            )
            approval_rows = list_approvals()
            if not approval_rows:
                st.info("No drafts awaiting review.")
            for item in approval_rows:
                status_label = item["status"].upper()
                with st.expander(f"{status_label} · {item['title']} · {item['approval_id'][:8]}"):
                    st.caption(
                        f"Type: {item['action_type']} · Company: {item['company'] or '—'} · "
                        f"Role: {item['role'] or '—'} · Created: {item['created_at']}"
                    )
                    if not item["payload_integrity_ok"]:
                        st.error("Payload integrity check failed. Do not approve this item.")
                    draft_text = item["payload"].get("draft", "")
                    if draft_text:
                        st.markdown(draft_text)
                        st.download_button(
                            "Download draft",
                            data=draft_text,
                            file_name=f"review_{item['approval_id'][:8]}.md",
                            mime="text/markdown",
                            key=f"career_review_dl_{item['approval_id']}",
                        )
                    else:
                        st.json(item["payload"])
                    if item["status"] == "pending" and item["payload_integrity_ok"]:
                        note = st.text_input(
                            "Review note (optional)",
                            key=f"career_note_{item['approval_id']}",
                        )
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("Approve draft", key=f"career_approve_{item['approval_id']}"):
                                if decide_approval(item["approval_id"], "approved", note):
                                    st.success("Approval recorded. No external action was executed.")
                                    st.rerun()
                        with b2:
                            if st.button("Reject draft", key=f"career_reject_{item['approval_id']}"):
                                if decide_approval(item["approval_id"], "rejected", note):
                                    st.warning("Rejection recorded.")
                                    st.rerun()
                    elif item["status"] == "approved":
                        st.success("Approved by you — execution is still not performed.")
                    elif item["status"] == "rejected":
                        st.caption("Rejected. No external action was performed.")

        with sub_profile:
            st.markdown("### Candidate profile")
            st.caption("Keep this factual and consistent with your resume. The agent must not invent qualifications.")
            profile_form_data = get_profile() or saved_profile
            with st.form("career_profile_form"):
                profile_name = st.text_input("Name", value=profile_form_data.get("name", "Kalyan Kunduru"))
                profile_education = st.text_area("Education", value=profile_form_data.get("education", ""), height=80)
                profile_skills = st.text_area("Skills", value=profile_form_data.get("skills", ""), height=100)
                profile_projects = st.text_area("Projects / experience evidence", value=profile_form_data.get("projects", profile_form_data.get("project", "")), height=120)
                profile_experience = st.text_input("Experience summary", value=profile_form_data.get("experience", "Entry-level / fresher"))
                profile_years = st.number_input(
                    "Full-time experience (years)", min_value=0.0, max_value=40.0,
                    value=float(profile_form_data.get("years_experience", 0)), step=0.5
                )
                roles_text = st.text_area(
                    "Target roles (one per line)",
                    value="\n".join(profile_form_data.get("target_roles", profile_defaults["target_roles"])),
                    height=120
                )
                locations_text = st.text_input(
                    "Target locations (comma-separated)",
                    value=", ".join(profile_form_data.get("target_locations", ["Bengaluru", "Hyderabad"]))
                )
                salary_min = st.number_input("Minimum target salary (LPA)", min_value=0, max_value=100, value=int(profile_form_data.get("salary_min_lpa", 4)))
                salary_max = st.number_input("Maximum target salary (LPA)", min_value=0, max_value=100, value=int(profile_form_data.get("salary_max_lpa", 8)))
                save_profile_clicked = st.form_submit_button("Save candidate profile")
            if save_profile_clicked:
                updated_profile = {
                    "name": profile_name.strip(),
                    "education": profile_education.strip(),
                    "skills": profile_skills.strip(),
                    "projects": profile_projects.strip(),
                    "experience": profile_experience.strip(),
                    "years_experience": profile_years,
                    "target_roles": [x.strip() for x in roles_text.splitlines() if x.strip()],
                    "target_locations": [x.strip() for x in locations_text.split(",") if x.strip()],
                    "salary_min_lpa": salary_min,
                    "salary_max_lpa": salary_max,
                }
                if salary_max and salary_min and salary_max < salary_min:
                    st.error("Maximum salary must be greater than or equal to minimum salary.")
                else:
                    save_profile(updated_profile)
                    st.success("Candidate profile saved to the career database.")
                    st.rerun()

            st.markdown("---")
            st.markdown("**Audit trail**")
            audit = list_audit_events(30)
            if audit:
                audit_frame = pd.DataFrame([
                    {
                        "Time (UTC)": event["created_at"],
                        "Entity": event["entity_type"],
                        "Event": event["event_type"],
                        "ID": event["entity_id"][:8],
                    }
                    for event in audit
                ])
                st.dataframe(audit_frame, use_container_width=True, hide_index=True)
            else:
                st.caption("No audit events yet.")
