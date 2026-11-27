"""Happenstance Network Search API client.

Uses the vendor's official REST API. Search creation costs 2 Happenstance credits;
polling a search uses GET. API keys are read from environment/secrets and never
written to the job database or included in error messages.
"""
from __future__ import annotations

import os
from typing import Any

import requests

HAPPENSTANCE_HOME = "https://happenstance.ai/"
HAPPENSTANCE_MCP_URL = "https://happenstance.ai/mcp"
HAPPENSTANCE_CHATGPT_DOCS = "https://developer.happenstance.ai/mcp/chatgpt"
HAPPENSTANCE_API_BASE = "https://api.happenstance.ai/v1"
SEARCH_COST_CREDITS = 2


class HappenstanceError(RuntimeError):
    pass


def get_api_key() -> str:
    key = os.getenv("HAPPENSTANCE_API_KEY", "").strip()
    if key:
        return key
    try:
        import streamlit as st
        return str(st.secrets.get("HAPPENSTANCE_API_KEY", "")).strip()
    except Exception:
        return ""


def connection_status() -> dict[str, str | bool]:
    api_key = get_api_key()
    return {
        "available": True,
        "api_key_configured": bool(api_key),
        "api_ready": bool(api_key),
        "mcp_url": HAPPENSTANCE_MCP_URL,
        "docs_url": HAPPENSTANCE_CHATGPT_DOCS,
        "message": (
            "Happenstance API key configured. Network searches require an explicit button click."
            if api_key else
            "Add HAPPENSTANCE_API_KEY to Streamlit secrets or your server environment to enable direct network search."
        ),
    }


def _request(method: str, path: str, *, payload: dict[str, Any] | None = None,
             params: dict[str, str] | None = None) -> dict[str, Any]:
    api_key = get_api_key()
    if not api_key:
        raise HappenstanceError(
            "Happenstance API key is not configured. Add HAPPENSTANCE_API_KEY in Streamlit secrets."
        )
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    try:
        response = requests.request(
            method,
            f"{HAPPENSTANCE_API_BASE}{path}",
            headers=headers,
            json=payload,
            params=params,
            timeout=(5, 30),
        )
    except requests.RequestException as exc:
        raise HappenstanceError(f"Could not reach Happenstance: {exc.__class__.__name__}") from exc

    if not response.ok:
        try:
            error = response.json()
            if not isinstance(error, dict):
                error = {}
        except ValueError:
            error = {}
        status = response.status_code
        detail = error.get("detail") or error.get("title") or "The request was rejected."
        if status == 401:
            detail = "Happenstance rejected the API key. Check the key in your app secrets."
        elif status == 402:
            detail = "Happenstance reports insufficient credits. Check your account usage and billing."
        elif status == 429:
            detail = "Happenstance has too many searches running. Wait for one to finish and retry."
        elif status >= 500:
            detail = "Happenstance is temporarily unavailable. Retry later."
        raise HappenstanceError(f"Happenstance API error ({status}): {detail}")

    try:
        data = response.json()
    except ValueError as exc:
        raise HappenstanceError("Happenstance returned an unreadable response.") from exc
    if not isinstance(data, dict):
        raise HappenstanceError("Happenstance returned an unexpected response format.")
    return data



def get_usage() -> dict[str, Any]:
    """Return Happenstance credit balance. This is a read-only endpoint."""
    return _request("GET", "/usage")


def create_network_search(text: str, *, include_my_connections: bool = True,
                          include_friends_connections: bool = False,
                          group_ids: list[str] | None = None) -> dict[str, Any]:
    query = text.strip()
    if not query:
        raise ValueError("Search query cannot be empty.")
    payload: dict[str, Any] = {
        "text": query,
        "include_my_connections": bool(include_my_connections),
        "include_friends_connections": bool(include_friends_connections),
    }
    if group_ids:
        payload["group_ids"] = [str(item) for item in group_ids if str(item).strip()]
    return _request("POST", "/search", payload=payload)


def get_network_search(search_id: str, page_id: str | None = None) -> dict[str, Any]:
    safe_id = str(search_id).strip()
    if not safe_id or "/" in safe_id or "?" in safe_id:
        raise ValueError("A valid Happenstance search ID is required.")
    params = {"page_id": page_id} if page_id else None
    return _request("GET", f"/search/{safe_id}", params=params)


def referral_search_prompt(company: str, role: str, city: str) -> str:
    company = company.strip() or "companies hiring entry-level candidates"
    role = role.strip() or "entry-level software and AI roles"
    city = city.strip() or "Bengaluru or Hyderabad"
    return (
        f"Find people at {company}, especially recruiters, hiring managers and engineers "
        f"who can help with {role} opportunities in {city}. Prioritize direct connections "
        "and mutual introduction paths. Return each person's current role, company, "
        "profile link and shared connection names when available. Do not assume anyone "
        "is hiring unless the search result supports it."
    )


def flatten_search_results(data: dict[str, Any]) -> list[dict[str, str | float]]:
    """Create a compact, UI-safe representation without storing raw personal profiles."""
    mutuals = data.get("mutuals") or []
    people = data.get("results") or []
    rows: list[dict[str, str | float]] = []
    for person in people:
        if not isinstance(person, dict):
            continue
        social = person.get("socials") or {}
        mutual_names = []
        for ref in person.get("mutuals") or []:
            if isinstance(ref, dict):
                index = ref.get("index")
                if isinstance(index, int) and 0 <= index < len(mutuals):
                    name = mutuals[index].get("name")
                    if name:
                        mutual_names.append(str(name))
        rows.append({
            "name": str(person.get("name") or "Unknown person"),
            "title": str(person.get("current_title") or ""),
            "company": str(person.get("current_company") or ""),
            "summary": str(person.get("summary") or ""),
            "linkedin_url": str(social.get("linkedin_url") or ""),
            "happenstance_url": str(social.get("happenstance_url") or ""),
            "mutuals": ", ".join(mutual_names),
            "relevance_score": float(person.get("weighted_traits_score") or 0),
        })
    return rows
