# ◆ AI Career Suite

**An open-source AI-powered career toolkit** — coach, resume tailor, interview prep, job scraper, and multi-agent research, all in one app. Built solo, runs on free APIs, deployed live.

🔗 **[Live Demo →](https://ai-agent-2026-cttqmjzrumpwju6psuzkqv.streamlit.app)**

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA%203.3-orange)

---

## What it does

| Agent | What it does |
|---|---|
| 🧠 **Career Coach** | Persistent-memory chat. Upload any PDF (resume, job posting) and ask questions about it. |
| 📄 **Resume Tailor** | Paste a job description → get ATS keywords, rewritten bullet points, and a tailored summary. Download as `.txt` or `.docx`. |
| 🎤 **Interview Prep** | Practice with real questions, get scored feedback, track your score history over time. |
| 🔍 **Job Scraper** | Search live AI/ML jobs in Bengaluru (or anywhere), with clickable apply links and CSV export. |
| 🤖 **Multi-Agent Crew** | Three agents work in sequence — Researcher → Resume Writer → Interview Coach — to fully prep you for one specific company + role. |

Plus: dark/light theme toggle, editable profile (used across all agents), masked API key view, and full session export — all in **Settings**.

---

## Tech stack

- **Python 3.12**
- **Streamlit** — UI framework
- **Groq API** (LLaMA 3.3-70B) — fast, free-tier LLM inference
- **JobSpy** — live job scraping
- **python-docx**, **pypdf** — document generation and reading
- **Pandas** — data handling

---

## Run it locally

```bash
git clone https://github.com/kundurukalyan945-max/ai-agent-2026.git
cd ai-agent-2026
pip install -r requirements.txt
```

Create a `.env` file in the root folder:

