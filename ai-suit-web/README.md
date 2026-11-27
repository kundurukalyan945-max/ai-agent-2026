# Kalyan.AI — Vercel Career Agent

This folder contains the standalone HTML/CSS/JavaScript interface deployed at [ai-suit-web.vercel.app](https://ai-suit-web.vercel.app). The Career Agent is added to this existing UI; its navy/blue glass design and original agent navigation remain in place.

## Vercel project settings

Set the Vercel project's **Root Directory** to \`ai-suit-web\`. The folder contains the static \`index.html\`, the serverless API under \`api/\`, and this package manifest.

Install these environment variables in Vercel → Project → Settings → Environment Variables. Apply them to the Production environment (and Preview only if desired):

| Name | Required | Purpose |
|---|---:|---|
| \`APP_ACCESS_PASSWORD\` | Yes | Strong private passphrase used to unlock the Career Agent. Use at least 12 characters. |
| \`CAREER_DATABASE_URL\` | Yes | Supabase/PostgreSQL connection URL. Prefer the Supabase Session Pooler URI for IPv4-compatible hosting. |
| \`GROQ_API_KEY\` | Yes | Server-side Groq API key used to generate job-specific preparation packs and networking drafts. |
| \`GROQ_MODEL\` | No | Defaults to \`openai/gpt-oss-120b\`. |
| \`HAPPENSTANCE_API_KEY\` | No | Enables people-network search and credit checks. |

Do not put secret values in \`index.html\`, source control, client-side storage, or chat. If the database password contains reserved URL characters, percent-encode them when forming the PostgreSQL URI. After changing environment variables, redeploy the Vercel project.

## Features in the Career Agent tab

- Persistent candidate profile, job intake by CSV or manual entry, URL deduplication, fit scoring, and a job-status pipeline.
- Import-ready CSV support for Daily Fresher Job Radar output.
- Job-specific preparation packs, stored in the approval queue for review.
- Happenstance people-network search, credit checks, asynchronous result polling, and warm-introduction drafts.
- Audit history and integrity verification for approval payloads.

## Safety boundary

- No job application is submitted.
- No email or LinkedIn message is sent.
- Recording approval/rejection only records the user's decision; it never triggers an external action.
- Fit scoring is a transparent heuristic, not a hiring probability. Verify each job on the employer's official page.
- Happenstance search creation costs 2 API credits; Find More also costs credits. The UI requires explicit acknowledgement before starting a search.
- The Career Agent uses a single shared passphrase, not multi-user authentication or per-user data isolation. It is intended for one private user, not as a public multi-tenant service.
- The pre-existing Career Coach, Resume Tailor, Interview Prep and Multi-Agent Crew pages retain their previous browser-based behavior. Their Groq key storage is separate from the server-side Career Agent.

## Local development

Node.js 20+ is recommended.

\`\`\`bash
cd ai-suit-web
npm install
\`\`\`

The API requires the environment variables above and a reachable PostgreSQL database. The static UI can be opened locally, but its API calls require a local Vercel-compatible runtime or a deployed Vercel preview.
