# Full Career Agent — implementation foundation

This package extends the AI Career Suite without changing the existing Streamlit app entrypoint.

## Architecture

- **Job intake:** ingest verified job listings from Daily Fresher Job Radar and manual URLs.
- **Candidate profile:** durable, editable candidate profile stored locally in SQLite.
- **Matching:** deterministic eligibility and keyword scoring; AI explanations are advisory.
- **Preparation:** tailored resume/cover-letter drafts and interview preparation.
- **Network research:** optional Happenstance MCP/API adapter. No credentials are stored in source control.
- **Approval queue:** every external action is drafted first and requires an explicit, recorded approval.
- **Audit trail:** records preparation, approval, execution status, timestamps and action payload hashes.

## Safety boundary

This release intentionally does **not** submit job applications, send email, send LinkedIn messages, or contact recruiters. It provides a durable approval queue and explicit execution boundary. A later executor must require a fresh approval for each action and verify that the approved payload has not changed.

## Happenstance

Happenstance is an optional network-discovery integration, not a job-board scraper. Configure:
- `HAPPENSTANCE_MCP_URL` — MCP endpoint supplied by Happenstance.
- `HAPPENSTANCE_API_KEY` — optional credential when required by the endpoint.

Never commit tokens, personal contact exports, or mailbox contents. The adapter does not make network calls until configured and explicitly invoked.

## Local run

```bash
pip install -r requirements.txt
streamlit run app.py
```

The foundation uses only Python standard-library modules (SQLite, JSON, hashing, dataclasses). No additional package is required.
