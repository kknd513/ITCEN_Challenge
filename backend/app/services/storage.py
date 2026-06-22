from __future__ import annotations

import json
from typing import Any
from uuid import UUID

try:
    import psycopg2
    from psycopg2.extras import Json
except Exception:  # pragma: no cover - local fallback when psycopg2 is not installed
    psycopg2 = None  # type: ignore
    Json = lambda x: x  # type: ignore

from app.core.config import get_settings


def _connect():
    settings = get_settings()
    if not settings.database_url:
        return None
    if psycopg2 is None:
        return None
    try:
        return psycopg2.connect(settings.database_url)
    except Exception:
        return None


def save_incident(incident_id: str, input_text: str, incident_type: str) -> None:
    conn = _connect()
    if conn is None:
        return
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    id UUID PRIMARY KEY,
                    input_text TEXT NOT NULL,
                    incident_type TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
            cur.execute(
                "INSERT INTO incidents (id, input_text, incident_type) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING",
                (incident_id, input_text, incident_type),
            )
    finally:
        conn.close()


def save_analysis(incident_id: str, result: dict[str, Any]) -> None:
    conn = _connect()
    if conn is None:
        return
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id SERIAL PRIMARY KEY,
                    incident_id UUID,
                    result JSONB NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
            cur.execute("INSERT INTO analysis_results (incident_id, result) VALUES (%s, %s)", (incident_id, Json(result)))
    finally:
        conn.close()


def save_report(report_id: str, incident_id: str, title: str, markdown: str) -> None:
    conn = _connect()
    if conn is None:
        return
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS reports (
                    id UUID PRIMARY KEY,
                    incident_id UUID,
                    title TEXT NOT NULL,
                    markdown TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
            cur.execute(
                "INSERT INTO reports (id, incident_id, title, markdown) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET markdown=EXCLUDED.markdown",
                (report_id, incident_id, title, markdown),
            )
    finally:
        conn.close()


def save_agent_logs(incident_id: str, agent_logs: list[dict[str, Any]]) -> None:
    conn = _connect()
    if conn is None:
        return
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_logs (
                    id BIGSERIAL PRIMARY KEY,
                    incident_id UUID,
                    server_key TEXT,
                    agent_name TEXT,
                    role TEXT,
                    status TEXT,
                    payload JSONB NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
            for payload in agent_logs:
                cur.execute(
                    """
                    INSERT INTO agent_logs (incident_id, server_key, agent_name, role, status, payload)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        incident_id,
                        payload.get("server_key"),
                        payload.get("agent_name"),
                        payload.get("role"),
                        payload.get("status"),
                        Json(payload),
                    ),
                )
    finally:
        conn.close()
