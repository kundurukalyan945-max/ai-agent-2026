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
from datetime import datetime

import pandas as pd

load_dotenv()

# ──────────────────────────────────────────────────────────
# CONFIGURATION — centralised so it's easy to update
# ──────────────────────────────────────────────────────────
MODEL_ID = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_INPUT_CHARS = 8_000     # truncate large inputs before sending
MAX_PDF_CHARS = 4_000       # truncate extracted PDF text
API_TIMEOUT = 30            # seconds

def get_groq_client():
    """Return a Groq client or None if the key is missing."""
    from groq import Groq
    key = os.getenv("GROQ_API_KEY", "").strip()
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
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
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

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Career Coach", "Resume Tailor", "Interview Prep", "Job Search", "Crew"])


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
