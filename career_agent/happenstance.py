"""Happenstance setup metadata and safe network-research prompt helpers.

Happenstance exposes an official hosted MCP integration. Its documented connection
flow uses account sign-in/OAuth; this Streamlit app does not collect Happenstance
passwords or pretend that the user is connected when the OAuth handshake is absent.
"""
from __future__ import annotations

import os

HAPPENSTANCE_HOME = "https://happenstance.ai/"
HAPPENSTANCE_MCP_URL = "https://happenstance.ai/mcp"
HAPPENSTANCE_CHATGPT_DOCS = "https://developer.happenstance.ai/mcp/chatgpt"


def connection_status() -> dict[str, str | bool]:
    # An API key is not interchangeable with an MCP OAuth connection.
    has_api_key = bool(os.getenv("HAPPENSTANCE_API_KEY", "").strip())
    return {
        "available": True,
        "connected_to_this_app": False,
        "api_key_configured": has_api_key,
        "mcp_url": HAPPENSTANCE_MCP_URL,
        "docs_url": HAPPENSTANCE_CHATGPT_DOCS,
        "message": (
            "Happenstance is available as an official ChatGPT integration. "
            "This standalone Streamlit app has not completed a separate OAuth/API connection."
        ),
    }


def referral_search_prompt(company: str, role: str, city: str) -> str:
    company = company.strip() or "target companies"
    role = role.strip() or "entry-level software and AI roles"
    city = city.strip() or "Bengaluru or Hyderabad"
    return (
        f"Search my Happenstance network for people who work at {company} or can "
        f"introduce me to recruiters, hiring managers, or engineers hiring for {role} "
        f"in {city}. Prioritize genuine warm paths and explain the connection path. "
        "Return only information available in my connected network; do not guess email "
        "addresses or claim a referral is guaranteed."
    )
