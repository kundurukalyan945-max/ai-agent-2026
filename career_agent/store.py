"""SQLite/PostgreSQL persistence for jobs, profile, approvals and audit events.

Set CAREER_DATABASE_URL to a PostgreSQL/Supabase DSN for durable hosted storage.
Otherwise a local SQLite file is used. Never commit database files or credentials.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def database_path() -> Path:
    configured = os.getenv("CAREER_DB_PATH", "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / "career_agent.sqlite3"


def _secret(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        import streamlit as st
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def database_url() -> str:
    return _secret("CAREER_DATABASE_URL")


def database_backend() -> str:
    """Return a safe backend label without revealing a connection string."""
    dsn = database_url()
    return "PostgreSQL (remote DSN configured)" if dsn.startswith(("postgres://", "postgresql://")) else "SQLite (local file)"


class _PostgresCompat:
    """Small adapter so the repository layer can keep qmark placeholders."""
    def __init__(self, dsn: str):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError(
                "CAREER_DATABASE_URL is set but psycopg is missing. Install requirements.txt."
            ) from exc
        self._conn = psycopg.connect(
            dsn,
            row_factory=dict_row,
            connect_timeout=10,
            sslmode="require",
            prepare_threshold=None,
        )

    def execute(self, statement: str, params: tuple | list = ()):
        return self._conn.execute(statement.replace("?", "%s"), params)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def _initialize(conn: Any) -> None:
    statements = [
        """CREATE TABLE IF NOT EXISTS candidate_profile (
            profile_key TEXT PRIMARY KEY,
            payload_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            dedupe_key TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL DEFAULT '',
            work_mode TEXT NOT NULL DEFAULT '',
            url TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT 'manual',
            description TEXT NOT NULL DEFAULT '',
            date_posted TEXT NOT NULL DEFAULT '',
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS approvals (
            approval_id TEXT PRIMARY KEY,
            action_type TEXT NOT NULL,
            title TEXT NOT NULL,
            company TEXT NOT NULL DEFAULT '',
            role TEXT NOT NULL DEFAULT '',
            payload_json TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            reviewer_note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            decided_at TEXT NOT NULL DEFAULT ''
        )""",
        """CREATE TABLE IF NOT EXISTS audit_events (
            event_id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            detail_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""",
        "CREATE INDEX IF NOT EXISTS idx_jobs_updated ON jobs(updated_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_events(created_at DESC)",
    ]
    for statement in statements:
        conn.execute(statement)


@contextmanager
def _connect():
    dsn = os.getenv("CAREER_DATABASE_URL", "").strip()
    conn: Any
    if dsn.startswith(("postgres://", "postgresql://")):
        conn = _PostgresCompat(dsn)
    else:
        path = database_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
    try:
        _initialize(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _audit(conn: Any, entity_type: str, entity_id: str,
           event_type: str, detail: dict[str, Any] | None = None) -> None:
    conn.execute(
        "INSERT INTO audit_events VALUES (?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), entity_type, entity_id, event_type, _json(detail or {}), utc_now()),
    )


def get_profile() -> dict[str, Any]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT payload_json FROM candidate_profile WHERE profile_key = 'default'"
        ).fetchone()
    return json.loads(row["payload_json"]) if row else {}


def save_profile(profile: dict[str, Any]) -> None:
    clean = dict(profile)
    with _connect() as conn:
        conn.execute(
            """INSERT INTO candidate_profile(profile_key, payload_json, updated_at)
               VALUES('default', ?, ?)
               ON CONFLICT(profile_key) DO UPDATE SET
                 payload_json=excluded.payload_json, updated_at=excluded.updated_at""",
            (_json(clean), utc_now()),
        )
        _audit(conn, "profile", "default", "profile_saved", {"fields": sorted(clean.keys())})


def _job_dedupe_key(job: dict[str, Any]) -> str:
    url = str(job.get("url") or job.get("job_url") or "").strip()
    if url:
        return "url:" + url.lower().rstrip("/")
    key = "|".join(str(job.get(k, "")).strip().lower()
                   for k in ("company", "title", "location"))
    return "fields:" + hashlib.sha256(key.encode("utf-8")).hexdigest()


def add_job(job: dict[str, Any]) -> str:
    normalized = {
        "title": str(job.get("title") or "Untitled role").strip(),
        "company": str(job.get("company") or "Unknown company").strip(),
        "location": str(job.get("location") or "").strip(),
        "work_mode": str(job.get("work_mode") or "").strip(),
        "url": str(job.get("url") or job.get("job_url") or "").strip(),
        "source": str(job.get("source") or "manual").strip(),
        "description": str(job.get("description") or "").strip(),
        "date_posted": str(job.get("date_posted") or "").strip(),
    }
    dedupe = _job_dedupe_key(normalized)
    with _connect() as conn:
        existing = conn.execute("SELECT job_id FROM jobs WHERE dedupe_key = ?", (dedupe,)).fetchone()
        if existing:
            job_id = existing["job_id"]
            conn.execute(
                """UPDATE jobs SET title=?, company=?, location=?, work_mode=?, url=?,
                   source=?, description=?, date_posted=?, payload_json=?, updated_at=?
                   WHERE job_id=?""",
                (normalized["title"], normalized["company"], normalized["location"],
                 normalized["work_mode"], normalized["url"], normalized["source"],
                 normalized["description"], normalized["date_posted"], _json(normalized),
                 utc_now(), job_id),
            )
            _audit(conn, "job", job_id, "job_refreshed", {"source": normalized["source"]})
            return job_id

        job_id = str(uuid.uuid4())
        now = utc_now()
        conn.execute(
            """INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (job_id, dedupe, normalized["title"], normalized["company"],
             normalized["location"], normalized["work_mode"], normalized["url"],
             normalized["source"], normalized["description"], normalized["date_posted"],
             _json(normalized), now, now),
        )
        _audit(conn, "job", job_id, "job_added", {"source": normalized["source"]})
    return job_id


def list_jobs(limit: int = 200) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM jobs ORDER BY updated_at DESC LIMIT ?", (max(1, min(limit, 1000)),)
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["payload"] = json.loads(item.pop("payload_json"))
        result.append(item)
    return result


def create_approval(action_type: str, title: str, payload: dict[str, Any],
                    company: str = "", role: str = "") -> str:
    """Create a pending review item; creation never executes an external action."""
    approval_id = str(uuid.uuid4())
    payload_json = _json(payload)
    digest = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    with _connect() as conn:
        conn.execute(
            """INSERT INTO approvals
               (approval_id, action_type, title, company, role, payload_json,
                payload_sha256, status, reviewer_note, created_at, decided_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', '', ?, '')""",
            (approval_id, action_type, title, company, role, payload_json, digest, utc_now()),
        )
        _audit(conn, "approval", approval_id, "draft_created", {
            "action_type": action_type, "payload_sha256": digest,
        })
    return approval_id


def list_approvals(status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    with _connect() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM approvals WHERE status=? ORDER BY created_at DESC LIMIT ?",
                (status, max(1, min(limit, 500))),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM approvals ORDER BY created_at DESC LIMIT ?",
                (max(1, min(limit, 500)),),
            ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["payload"] = json.loads(item.pop("payload_json"))
        item["payload_integrity_ok"] = (
            hashlib.sha256(_json(item["payload"]).encode("utf-8")).hexdigest()
            == item["payload_sha256"]
        )
        result.append(item)
    return result


def decide_approval(approval_id: str, decision: str, reviewer_note: str = "") -> bool:
    """Record review only. Approval does not send messages or submit applications."""
    if decision not in {"approved", "rejected"}:
        raise ValueError("decision must be 'approved' or 'rejected'")
    with _connect() as conn:
        row = conn.execute(
            "SELECT status, payload_sha256, payload_json FROM approvals WHERE approval_id=?",
            (approval_id,),
        ).fetchone()
        if not row or row["status"] != "pending":
            return False
        actual = hashlib.sha256(row["payload_json"].encode("utf-8")).hexdigest()
        if actual != row["payload_sha256"]:
            raise ValueError("Approval payload integrity check failed")
        conn.execute(
            "UPDATE approvals SET status=?, reviewer_note=?, decided_at=? WHERE approval_id=? AND status='pending'",
            (decision, reviewer_note.strip(), utc_now(), approval_id),
        )
        _audit(conn, "approval", approval_id, decision, {
            "payload_sha256": row["payload_sha256"], "execution": "not_performed",
        })
    return True


def list_audit_events(limit: int = 50) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_events ORDER BY created_at DESC LIMIT ?",
            (max(1, min(limit, 500)),),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["detail"] = json.loads(item.pop("detail_json"))
        result.append(item)
    return result
