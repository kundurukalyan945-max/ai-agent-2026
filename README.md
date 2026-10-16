# ◆ AI Career Suite

**An open-source AI-powered career toolkit** — coach, resume tailor, interview prep, job scraper, and company research workflow, all in one app. Built solo, runs on free APIs, deployed live.

🌐 **[Web App →](https://ai-suit-web.vercel.app)** — works on mobile + desktop, no install needed  
🔗 **[Streamlit Demo →](https://ai-agent-2026-cttqmjzrumpwju6psuzkqv.streamlit.app)**

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA%203.3-orange)
![Vercel](https://img.shields.io/badge/Deployed-Vercel-black?logo=vercel)

---

## What it does

| Tab | What it does |
|---|---|
| 🧠 **Career Coach** | Chat with an AI that reads your uploaded PDF (resume or job posting). Chat history is session-only — it is not persisted between browser sessions. |
| 📄 **Resume Tailor** | Paste a job description → get ATS keywords, rewritten bullet points, and a tailored summary. Download as `.txt`. |
| 🎤 **Interview Prep** | Practice with AI/ML questions, get scored feedback, track your score history within the session. |
| 🔍 **Job Scraper** | **Streamlit only** — live scraping via JobSpy with CSV export. The web app shows sample data and links to the Python backend for real results. |
| 🤖 **Company Research Workflow** | Three sequential LLM calls (Researcher → Resume Writer → Interview Coach) that together produce a targeted preparation report for one company and role. This is a sequential pipeline, not an autonomous multi-agent system. |

Settings: dark/light theme toggle, candidate profile editor (used by Resume Tailor and Workflow tabs), API key management, session export.

---

## What it does NOT do

- **No persistent memory** — chat history is session-scoped; closing the tab clears it.
- **No live job data in the web app** — the web version shows sample data. Run `streamlit run app.py` locally for real job listings.
- **No autonomous agents** — the Workflow tab is three sequential Groq API calls, not a CrewAI or multi-agent system.

---

## Live deployments

| Version | URL | Stack |
|---|---|---|
| 🌐 Web App | [ai-suit-web.vercel.app](https://ai-suit-web.vercel.app) | HTML + JS + Vercel |
| 🐍 Streamlit App | [streamlit deploy](https://ai-agent-2026-cttqmjzrumpwju6psuzkqv.streamlit.app) | Python + Streamlit Cloud |

---

## Tech stack

- **Python 3.12** + **Streamlit** — main app
- **HTML/CSS/JS** — web app (zero frameworks, pure vanilla)
- **Groq API** (`llama-3.3-70b-versatile`) — fast, free-tier LLM inference
- **JobSpy** — live job scraping (Python backend only)
- **python-docx**, **pypdf**, **PDF.js** — document handling
- **Pandas** — data handling
- **Vercel** — web deployment

---

## Run locally (Python/Streamlit)

```bash
git clone https://github.com/kundurukalyan945-max/ai-agent-2026.git
cd ai-agent-2026
pip install -r requirements.txt
```

Create a `.env` file (see `.env.example`):

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

Get a free key at [console.groq.com](https://console.groq.com) — takes 30 seconds.

```bash
streamlit run app.py
```

## Run locally (web version)

Open `ai-suit-web/index.html` in any browser. Enter your Groq API key in Settings when prompted. No server needed. The key is stored in browser `localStorage` only.

---

## Run tests

```bash
pip install pytest
pytest tests/ -v
```

The test suite covers XSS escaping, API key masking, missing-key handling, error classification, model config, docx generation, and profile defaults — without making any real API calls.

---

## Configuration

| Variable | Default | Notes |
|---|---|---|
| `GROQ_API_KEY` | *(required)* | Free at console.groq.com |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Override to use a different Groq model |

---

## About the builder

**Kundura Kalyan** — B.Tech CSE (AI/ML), SVCE Bengaluru, 2026.

Built as a real learning project and a tool for my own AI/ML job search. Every feature solves a real problem I faced.

- 🔗 [LinkedIn](https://www.linkedin.com/in/kalyan-kunduru-84487b287)
- 💻 [GitHub](https://github.com/kundurukalyan945-max)

---

## Contributing

Issues and PRs welcome. If you use this for your own job search, I'd love to hear about it — open an issue and say hi.

---

## License

MIT — see [LICENSE](LICENSE). Free to use, modify, and share with attribution.
