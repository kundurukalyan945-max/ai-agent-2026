<div align="center">

# ◆ AI Career Suite

**Your AI-powered career co-pilot. Built solo. Deployed live. Actually useful.**

[![Live Demo](https://img.shields.io/badge/🌐%20Web%20App-Live-4F8EFF?style=for-the-badge)](https://ai-suit-web.vercel.app)
[![Streamlit](https://img.shields.io/badge/🐍%20Streamlit%20App-Live-FF4B4B?style=for-the-badge)](https://ai-agent-2026-cttqmjzrumpwju6psuzkqv.streamlit.app)

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![Groq](https://img.shields.io/badge/LLM-LLaMA%203.3%2070B-F55036?style=flat-square)
![Vercel](https://img.shields.io/badge/Deployed-Vercel-000000?style=flat-square&logo=vercel)
![License](https://img.shields.io/badge/License-MIT-2ECC8A?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-43%20passing-2ECC8A?style=flat-square)

</div>

---

> **tl;dr** — AI Career Suite combines career coaching, resume tailoring, interview practice, job search and company research with a persistent Career Agent workspace for job tracking, fit scoring, application-pack drafts, referral preparation and human-reviewed approvals.

---

## ✨ What's inside

| Agent | Vibe | What it actually does |
|---|---|---|
| 🧠 **Career Coach** | Your AI bestie for career Qs | Chat with context — upload your resume or a job posting as PDF, ask anything |
| 📄 **Resume Tailor** | ATS go brrr | Paste a JD → get rewritten bullets, ATS keywords, tailored summary → download `.txt` |
| 🎤 **Interview Prep** | No more blanking in interviews | AI/ML question bank, scored answers, track improvement within session |
| 🔍 **Job Scraper** | Python backend only | Live scraping via JobSpy → CSV export. Web app shows sample data |
| 🤖 **Company Research** | 3-step sequential workflow | Researcher → Resume Writer → Interview Coach, one pipeline, one click |
| 🧭 **Career Agent** | Persistent career workspace | Candidate profile, saved jobs, transparent fit scoring, preparation packs, referral drafts, approval queue and audit trail |

> **⚠️ Keeping it real:** The original five tabs mostly use session state; the new Career Agent tab persists its profile, jobs and review records in SQLite. Company Research remains a sequential LLM workflow, not a fully autonomous multi-agent runtime. The review queue records approval but this release does not submit applications or send messages. The web frontend does not scrape live jobs.

---

## 🚀 Try it now

No install needed → **[ai-suit-web.vercel.app](https://ai-suit-web.vercel.app)**

1. Open the link
2. Go to **Settings → API Key**
3. Paste your free Groq key from [console.groq.com](https://console.groq.com) (takes 30 sec)
4. Start cooking 🔥

---


## 🧭 Career Agent workspace

The **Career Agent** tab adds a persistent job-search workspace alongside the original tools.

- Store and edit your candidate profile, target roles, cities and salary range.
- Import job results from the existing Job Search tab or a CSV from your Daily Job Radar.
- Deduplicate jobs by URL and calculate an explainable keyword/location fit indicator.
- Generate a truthful job-specific preparation pack: tailored summary, project bullets, keyword suggestions, cover-letter draft, interview topics and verification checklist.
- Prepare referral/recruiter messages from Happenstance findings.
- Review, approve or reject every draft. Decisions are hashed and recorded in an audit trail.

### Happenstance

Happenstance is an optional network-research source, not the job scraper. Connect it through its official ChatGPT integration using the vendor's [connection guide](https://developer.happenstance.ai/mcp/chatgpt). The Streamlit app can call the Happenstance REST API directly when HAPPENSTANCE_API_KEY is configured in Streamlit Secrets. Search creation costs 2 credits; the UI requires an explicit credit confirmation, then polls the search status. Results stay in the current app session. The app does not send messages.

### Hosted configuration\n\nAdd these keys in Streamlit Community Cloud → App → Settings → Secrets (or as server environment variables):\n\n- `CAREER_DATABASE_URL`: PostgreSQL connection string from Supabase Dashboard → Connect.\n- `HAPPENSTANCE_API_KEY`: API key from Happenstance developer settings. A search costs 2 credits.\n- `GROQ_API_KEY`: existing Groq LLM key.\n\nUse deployment secrets, not `.env` or committed configuration, in hosted environments.\n\n### Approval and execution boundary

Approval is recorded in the local database only. It does **not** submit a job application, send an email, or message a recruiter. A separate executor, account connection and per-action confirmation are required before external actions can be enabled. No automatic external action is performed by this release.

### Persistent storage

SQLite is used by default at career_agent.sqlite3 in the project root. Set CAREER_DATABASE_URL to a PostgreSQL/Supabase connection string stored in Streamlit Secrets. Local SQLite is for development only; generated files and app-local files on Streamlit Community Cloud are not guaranteed to persist across user sessions. For IPv4-only Community Cloud networking, copy the Supabase Session Pooler connection string from Dashboard → Connect. Keep the password out of GitHub.

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

**43 tests. 0 real API calls.** Covers XSS escaping, key masking, missing-key handling, error classification, model config, docx generation, and profile defaults. Streamlit is stubbed so tests run anywhere.

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
