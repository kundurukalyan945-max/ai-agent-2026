<div align="center">

# ◆ AI Career Suite

### Your career toolkit for the whole job hunt.

**Built for the real job search — not just another AI demo.**

A practical workspace for career coaching, resume tailoring, interview practice, job discovery and application preparation. Now with a persistent Career Agent to keep your opportunities, drafts and decisions organised.

<p>
  <a href="https://ai-suit-web.vercel.app"><strong>🌐 Open the Web App</strong></a>
  &nbsp;·&nbsp;
  <a href="https://ai-agent-2026-cttqmjzrumpwju6psuzkqv.streamlit.app"><strong>🐍 Open the Streamlit App</strong></a>
  &nbsp;·&nbsp;
  <a href="https://github.com/kundurukalyan945-max/ai-agent-2026"><strong>⭐ View Source</strong></a>
</p>

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-20%2B-339933?logo=nodedotjs&logoColor=white)
![Groq](https://img.shields.io/badge/LLM-Groq%20API-F55036)
![Vercel](https://img.shields.io/badge/Deploy-Vercel-000000?logo=vercel&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-48%20passing-2ECC8A)
![License](https://img.shields.io/badge/License-MIT-2ECC8A)

</div>

---

## Why I built this

I built AI Career Suite for a simple reason: **I was building my own path into AI/ML, and I wanted better tools for the job search I was actually going through.**

Preparing for an entry-level role involves more than sending a resume. You need to figure out which roles fit your skills, understand job descriptions, tailor your project experience, practise interviews, research companies and keep track of applications. Those tasks are connected, but they often end up scattered across different tools.

I wanted one place to bring that workflow together.

The project started with the tools I personally needed: a career coach, resume tailor, interview practice, job search and company research. The Career Agent is the next step — turning that collection of helpers into a more organised workspace with a candidate profile, saved opportunities, explainable fit indicators, preparation drafts and a review history.

**The point is not to auto-apply everywhere or promise a shortcut to a job.** It is to reduce repetitive work, make preparation more focused and keep the important decisions in your hands.

I built it to solve my own problem first. I'm sharing it so other students, freshers and early-career candidates can use it, learn from it and make it their own.

---

## What's inside

| Tool | What it does | Where it runs |
|---|---|---|
| 🧠 **Career Coach** | Ask career questions with profile context. Upload a resume or job-posting PDF and discuss it with the coach. | Web + Streamlit |
| 📄 **Resume Tailor** | Work from a job description to generate ATS keyword suggestions, tailored project bullets and a role-specific summary. | Web + Streamlit |
| 🎤 **Interview Prep** | Practise AI/ML questions, get structured feedback and track your scores. | Web + Streamlit |
| 🔍 **Job Search** | Search job listings with the Python/JobSpy workflow and export results to CSV. The web UI uses demo/sample listings only. | Streamlit live search; Web demo |
| 🤖 **Multi-Agent Crew** | Run a three-step company and role preparation workflow: Researcher → Resume Writer → Interview Coach. | Web + Streamlit |
| 🚀 **Career Agent** | Maintain a candidate profile, save and rank jobs, prepare application packs, research professional connections and review drafts. | Web + Streamlit |

### Two ways to use the suite

- **Web app (ai-suit-web/)** — the original navy-and-blue interface, built with HTML, CSS and JavaScript. It is deployed on Vercel. The Career Agent uses a server-side API.
- **Python app (app.py)** — the Streamlit version. It includes the JobSpy-based live job search, CSV workflows and .docx resume export.

The two interfaces share the same overall career workflow, but some features are platform-specific. In particular, **the Vercel Job Scraper page displays sample data; use the Streamlit app for the Python JobSpy search.**

---

## 🚀 Career Agent: from job link to review-ready preparation

The Career Agent is designed to make the job hunt easier to manage — without pretending that a fit score guarantees an interview.

### Job pipeline

- Keep an editable candidate profile with education, skills, projects, experience evidence, target roles and locations.
- Add verified job listings manually or import CSV files from Job Search or your Daily Fresher Job Radar.
- Consolidate repeated listings using their job URL.
- Track opportunities through a simple pipeline.
- View a transparent fit indicator based on detected skill overlap, target-role alignment and location.

### Application preparation

For a saved role, generate a job-specific preparation pack with:

- A fit summary and potential gaps.
- A tailored professional summary.
- Truthful project and experience bullet suggestions.
- Relevant ATS keyword suggestions.
- A cover-letter draft.
- Interview topics and a verification checklist.

The model is instructed to use the candidate information supplied to it. Review every generated detail and confirm it against your actual experience and the employer's original job listing before using it.

### Happenstance: people and network discovery

[Happenstance](https://happenstance.ai/) is an optional **professional-network search tool**, not a job board. It can help find relevant recruiters, hiring managers, engineers and possible introduction paths from the connections available to your Happenstance account.

- Check credit usage before searching.
- A new search costs **2 Happenstance credits**. Find More is a separate credit-consuming action.
- Upload your LinkedIn connections to Happenstance if you want it to search your own network.
- Use results to prepare a respectful networking draft.

Search results are held in the active app session; selected people and generated drafts can be saved for review. **The app does not send LinkedIn messages, emails or recruiter outreach.**

### Approval queue: you stay in control

Generated application packs and networking drafts go into a review queue. You can inspect, approve or reject each draft. The queue verifies the saved payload and records decisions in an audit trail.

**Approval means your decision was recorded. It does not mean an application was submitted or a message was sent.** This release has no external-action executor.

### Storage

The Career Agent supports:

- **SQLite** for local development.
- **PostgreSQL / Supabase** for hosted, persistent storage using CAREER_DATABASE_URL.

Use PostgreSQL/Supabase for durable hosted records. A local SQLite file or an app's temporary filesystem should not be treated as permanent storage on a hosted platform.

---

## Try it online

### Web app

Open **[ai-suit-web.vercel.app](https://ai-suit-web.vercel.app)**.

The original browser-based tools use a Groq key entered in **Settings → API Key**. That key is saved in the browser's localStorage and sent directly from the browser to Groq.

The **Career Agent is different**: its Groq key, database URL, Happenstance key and unlock password are configured as server-side Vercel environment variables. The browser-based key and server-side key are separate settings.

### Streamlit app

Open **[AI Career Suite on Streamlit](https://ai-agent-2026-cttqmjzrumpwju6psuzkqv.streamlit.app)**.

For the private Career Agent tab, configure APP_ACCESS_PASSWORD in Streamlit App Settings → Secrets. Hosted Streamlit and Vercel have separate environment-variable settings; adding a secret to one platform does not add it to the other.

---

## Run locally

### Python / Streamlit app

**Requirements:** Python 3.11 or 3.12.

    # Clone the repository
    git clone https://github.com/kundurukalyan945-max/ai-agent-2026.git
    cd ai-agent-2026

    # Create and activate a virtual environment (macOS / Linux)
    python3 -m venv .venv
    source .venv/bin/activate

    # Install dependencies
    pip install -r requirements.txt

    # Create your local environment file
    cp .env.example .env

    # Add your own GROQ_API_KEY and optional settings to .env
    # Then start the app
    streamlit run app.py

Get a Groq API key from [Groq Console](https://console.groq.com/).

### Environment variables

The following are configuration names only — **put your own values in .env locally or in your deployment's secret manager. Never commit real keys, passwords or database URLs.**

| Variable | Required for | Purpose |
|---|---|---|
| GROQ_API_KEY | AI features | Groq API key for model calls. |
| GROQ_MODEL | Optional | Model override. The app default is openai/gpt-oss-120b. Check Groq Console for current model availability and pricing. |
| APP_ACCESS_PASSWORD | Private Career Agent | Strong, unique passphrase for the Career Agent workspace. |
| CAREER_DATABASE_URL | Hosted persistence | PostgreSQL/Supabase connection URL. Prefer the Supabase Session Pooler URI where IPv4 compatibility is needed. |
| HAPPENSTANCE_API_KEY | Happenstance search | Enables direct people-network search and credit lookup. |
| CAREER_DB_PATH | Optional local setup | Custom path for the SQLite database file. |

Example local .env shape:

    GROQ_API_KEY=your_groq_key
    GROQ_MODEL=openai/gpt-oss-120b
    APP_ACCESS_PASSWORD=your_unique_private_passphrase
    CAREER_DATABASE_URL=postgresql://user:password@host:5432/database
    HAPPENSTANCE_API_KEY=your_happenstance_key

Leave out optional values you do not use. The .env file is gitignored.

---

## Deploy

### Vercel — web app

The Vercel project should use:

- **Repository:** kundurukalyan945-max/ai-agent-2026
- **Production branch:** main
- **Root Directory:** ai-suit-web
- **Runtime:** Node.js 20+

Add these variables in **Vercel → Project → Settings → Environment Variables**:

| Variable | Required | Notes |
|---|---:|---|
| APP_ACCESS_PASSWORD | Yes | Strong, unique Career Agent passphrase. |
| CAREER_DATABASE_URL | Yes | Supabase/PostgreSQL connection URL. |
| GROQ_API_KEY | Yes | Server-side Groq key for Career Agent generation. |
| HAPPENSTANCE_API_KEY | Optional | Enables Happenstance network search. |
| GROQ_MODEL | Optional | Defaults to openai/gpt-oss-120b. |

Select the environments where the variables are needed — **Production** and, when testing pull requests, **Preview**. Redeploy after changing environment variables.

If your Supabase password contains reserved URL characters, URL-encode those characters in the connection string. Keep the complete connection URL private.

### Streamlit Community Cloud — Python app

Deploy the repository using app.py as the app entry point and requirements.txt for dependencies.

Add the required values under **App → Settings → Secrets**. Use the same variable names shown above, but configure them separately from Vercel.

For persistent hosted Career Agent data, configure CAREER_DATABASE_URL with your PostgreSQL/Supabase URL. SQLite is the local development default; do not rely on a temporary hosted filesystem for permanent records.

---

## Tests

Run the Python test suite:

    pip install pytest
    pytest tests/ -v

**48 tests** cover the existing app, HTML escaping, key handling, model configuration, document generation, profile defaults, Career Agent storage and matching, approval integrity and Happenstance request handling. Tests use mocks and do not require real API calls.

GitHub Actions also checks the Python application on Python 3.11 and 3.12, plus JavaScript syntax for the Vercel API and web interface.

---

## Tech stack

| Layer | Technologies |
|---|---|
| Python app | Python 3.12, Streamlit, Groq SDK, JobSpy, pandas, pypdf, python-docx |
| Web interface | HTML, CSS, vanilla JavaScript, PDF.js |
| Vercel API | Node.js serverless function, PostgreSQL client (pg) |
| AI | Groq API, default model openai/gpt-oss-120b |
| Storage | SQLite for local development; PostgreSQL / Supabase for hosted persistence |
| Network research | Happenstance REST API |
| Deployment | Vercel (web) · Streamlit Community Cloud (Python) |
| Tests | pytest · GitHub Actions · Node.js syntax checks |

No React or Next.js is required for the web frontend. The interface stays lightweight and keeps the original visual design.

---

## Project structure

    ai-agent-2026/
    ├── ai-suit-web/
    │   ├── api/
    │   │   └── career-agent.js   # Vercel Career Agent API
    │   ├── index.html            # Original AI Career Suite web UI
    │   ├── package.json          # Node.js dependencies and runtime
    │   ├── vercel.json           # Vercel function configuration
    │   └── README.md             # Web deployment notes
    ├── career_agent/
    │   ├── store.py              # SQLite / PostgreSQL persistence
    │   ├── matching.py           # Explainable job-fit heuristic
    │   └── happenstance.py       # Happenstance API client
    ├── tests/
    │   ├── test_app.py
    │   ├── test_career_agent.py
    │   └── test_happenstance.py
    ├── app.py                    # Streamlit application
    ├── ai_coach.py               # Career Coach
    ├── resume_tailor.py          # Resume Tailor
    ├── interview_prep.py         # Interview Prep
    ├── job_scraper.py            # Python job search workflow
    ├── crew_agent.py             # Sequential company-prep workflow
    ├── requirements.txt
    ├── .env.example
    └── README.md

---

## Built by

**Kalyan Kunduru**  
B.Tech, Computer Science & Engineering (AI/ML) · Sri Venkateswara College of Engineering · 2026

This is a personal project built around a real job-search workflow. The features are shaped by the tasks I wanted to make easier in my own AI/ML career journey — and the goal is to keep improving it in public.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/kalyan-kunduru-84487b287)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/kundurukalyan945-max)

---

## Contributing

Issues, feedback and pull requests are welcome. Found a bug, have an idea or want to improve a workflow? Open an issue or submit a PR.

Please do not include API keys, passwords, personal contact exports or private candidate data in issues or commits.

## License

MIT — free to use, fork and adapt. Attribution is appreciated.
