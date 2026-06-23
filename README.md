# ◆ AI Career Suite

**An open-source AI-powered career toolkit** — coach, resume tailor, interview prep, job scraper, and multi-agent research, all in one app. Built solo, runs on free APIs, deployed live.

🌐 **[Web App →](https://ai-suit-web.vercel.app)** — works on mobile + desktop, no install needed
🔗 **[Streamlit Demo →](https://ai-agent-2026-cttqmjzrumpwju6psuzkqv.streamlit.app)**

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA%203.3-orange)
![Vercel](https://img.shields.io/badge/Deployed-Vercel-black?logo=vercel)

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

## Live Deployments

| Version | URL | Stack |
|---|---|---|
| 🌐 Web App | [ai-suit-web.vercel.app](https://ai-suit-web.vercel.app) | HTML + JS + Vercel |
| 🐍 Streamlit App | [streamlit deploy](https://ai-agent-2026-cttqmjzrumpwju6psuzkqv.streamlit.app) | Python + Streamlit Cloud |

---

## Tech stack

- **Python 3.12** + **Streamlit** — original app
- **HTML/CSS/JS** — web app (zero frameworks, pure vanilla)
- **Groq API** (LLaMA 3.3-70B) — fast, free-tier LLM inference
- **JobSpy** — live job scraping
- **python-docx**, **pypdf**, **PDF.js** — document handling
- **Pandas** — data handling
- **Vercel** — web deployment

---

## Run it locally (Python/Streamlit version)

```bash
git clone https://github.com/kundurukalyan945-max/ai-agent-2026.git
cd ai-agent-2026
pip install -r requirements.txt
```

Create a `.env` file in the root folder:

```
GROQ_API_KEY=your_key_here
```

Get a free Groq API key at [console.groq.com](https://console.groq.com) — takes 30 seconds.

Then run:

```bash
streamlit run app.py
```

## Run it locally (Web version)

Just open `ai-suit-web/index.html` in any browser. Enter your Groq API key in Settings when prompted. No server needed.

---

## About the builder

**Kundura Kalyan** — final-year B.Tech CSE (AI/ML) student at SVCE Bengaluru, graduating 2026.

I built this as both a real learning project and a tool I personally use for my own AI/ML job search. Every agent here solves a real problem I faced — tailoring resumes for each JD, practicing interview answers, tracking which companies to target. Built entirely with free tools.

- 🔗 [LinkedIn](https://www.linkedin.com/in/kalyan-kunduru-84487b287)
- 💻 [GitHub](https://github.com/kundurukalyan945-max)

---

## Contributing

Issues and PRs welcome. If you use this for your own job search, I'd love to hear about it — open an issue and say hi.

---

## License

MIT — see [LICENSE](LICENSE). Free to use, modify, and share with attribution.