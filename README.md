<div align="center">

# ◆ AI Career Suite

**Your AI-powered career co-pilot. Built solo. Deployed live. Actually useful.**

[![Live Demo](https://img.shields.io/badge/🌐%20Web%20App-Live-4F8EFF?style=for-the-badge)](https://ai-suit-web.vercel.app)
[![Streamlit](https://img.shields.io/badge/🐍%20Streamlit%20App-Live-FF4B4B?style=for-the-badge)](https://ai-agent-2026-cttqmjzrumpwju6psuzkqv.streamlit.app)

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![Groq](https://img.shields.io/badge/LLM-LLaMA%203.3%2070B-F55036?style=flat-square)
![Vercel](https://img.shields.io/badge/Deployed-Vercel-000000?style=flat-square&logo=vercel)
![License](https://img.shields.io/badge/License-MIT-2ECC8A?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-39%20passing-2ECC8A?style=flat-square)

</div>

---

> **tl;dr** — 5 AI agents in one app that actually help you land a job. Career coach, resume tailor, interview prep, job scraper, and a 3-step company research workflow. Runs on Groq's free API. No paid subscriptions, no fluff.

---

## ✨ What's inside

| Agent | Vibe | What it actually does |
|---|---|---|
| 🧠 **Career Coach** | Your AI bestie for career Qs | Chat with context — upload your resume or a job posting as PDF, ask anything |
| 📄 **Resume Tailor** | ATS go brrr | Paste a JD → get rewritten bullets, ATS keywords, tailored summary → download `.txt` |
| 🎤 **Interview Prep** | No more blanking in interviews | AI/ML question bank, scored answers, track improvement within session |
| 🔍 **Job Scraper** | Python backend only | Live scraping via JobSpy → CSV export. Web app shows sample data |
| 🤖 **Company Research** | 3-agent sequential workflow | Researcher → Resume Writer → Interview Coach, one pipeline, one click |

> **⚠️ Keeping it real:** No persistent memory (session only). No autonomous agents (sequential API calls, not CrewAI). No live jobs in the web app (use the Python version for that).

---

## 🚀 Try it now

No install needed → **[ai-suit-web.vercel.app](https://ai-suit-web.vercel.app)**

1. Open the link
2. Go to **Settings → API Key**
3. Paste your free Groq key from [console.groq.com](https://console.groq.com) (takes 30 sec)
4. Start cooking 🔥

---

## 🛠️ Run it locally (full Python version)

The Streamlit app has live job scraping + `.docx` resume export that the web app doesn't.

```bash
# Clone
git clone https://github.com/kundurukalyan945-max/ai-agent-2026.git
cd ai-agent-2026

# Install deps
pip install -r requirements.txt

# Set up your API key
cp .env.example .env
# → open .env, add your GROQ_API_KEY

# Run
streamlit run app.py
```

Get a **free** Groq key at [console.groq.com](https://console.groq.com) — LLaMA 3.3 70B is fast and free on their tier.

### Web version (zero setup)

```bash
# Just open in browser — no server needed
open ai-suit-web/index.html
```

---

## 🧪 Tests

```bash
pip install pytest
pytest tests/ -v
```

**39 tests. 0 real API calls.** Covers XSS escaping, key masking, missing-key handling, error classification, model config, docx generation, and profile defaults. Streamlit is stubbed so tests run anywhere.

---

## ⚙️ Config

| Variable | Required | Default | Notes |
|---|---|---|---|
| `GROQ_API_KEY` | ✅ Yes | — | Free at [console.groq.com](https://console.groq.com) |
| `GROQ_MODEL` | ❌ No | `llama-3.3-70b-versatile` | Swap to any Groq-supported model |

---

## 🏗️ Tech stack

```
Backend      →  Python 3.12 · Streamlit · Groq SDK · JobSpy · pandas · pypdf · python-docx
Frontend     →  Vanilla HTML/CSS/JS (zero frameworks) · PDF.js · glassmorphism UI
LLM          →  Groq API · LLaMA 3.3 70B Versatile (free tier)
Deployment   →  Vercel (web) · Streamlit Cloud (Python)
```

No React. No Next.js. No bloat. Just vibes and vanilla JS.

---

## 🔒 Security notes

- API key is stored in **your browser's `localStorage` only** — never sent anywhere except directly to `api.groq.com`
- All LLM output is HTML-escaped before rendering (XSS protected)
- `.env` is gitignored — your key never touches the repo
- No user data is collected or logged anywhere

---

## 📁 Project structure

```
ai-agent-2026/
├── app.py                  # Main Streamlit app
├── ai_coach.py             # Career coach agent logic
├── resume_tailor.py        # Resume tailoring agent
├── crew_agent.py           # 3-step company research workflow
├── requirements.txt
├── .env.example            # Copy → .env, add your key
├── tests/
│   └── test_app.py         # 39 tests
└── ai-suit-web/
    └── index.html          # Standalone web app (Vercel)
```

---

## 👤 Built by

**Kalyan Kunduru** — B.Tech CSE (AI/ML), SVCE Bengaluru, 2026.

Built this for my own AI/ML job search. Every feature is something I actually needed. If it helps you too, that's the whole point.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/kalyan-kunduru-84487b287)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat-square&logo=github)](https://github.com/kundurukalyan945-max)

---

## 🤝 Contributing

PRs and issues welcome. If you use this for your own job search — drop an issue and let me know how it went. Always down to improve it.

---

## 📄 License

MIT — free to use, fork, and ship. Attribution appreciated but not required.
