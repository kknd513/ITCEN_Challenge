from __future__ import annotations

from pathlib import Path
from typing import Any
import httpx

from app.core.config import get_settings

BASE_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = BASE_DIR / "data" / "mock_logs"


def _read_lines(filename: str) -> list[str]:
    path = LOG_DIR / filename
    if not path.exists():
        return []
    return [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def internal_agent_payload(role: str) -> dict[str, Any]:
    role_upper = role.upper()
    if role_upper in {"WEB", "WEB-01"}:
        return {
            "agent_name": "WEB-01",
            "role": "WEB",
            "status": "warning",
            "host": "WEB-01",
            "service": "Nginx Reverse Proxy",
            "metrics": {"cpu": "35%", "memory": "46%", "active_connections": 382, "upstream_5xx": 27},
            "logs": _read_lines("web-01-nginx-error.log"),
        }
    if role_upper in {"WAS", "WAS-01"}:
        return {
            "agent_name": "WAS-01",
            "role": "WAS",
            "status": "critical",
            "host": "WAS-01",
            "service": "Tomcat",
            "metrics": {"cpu": "78%", "memory": "82%", "active_threads": 200, "max_threads": 200},
            "logs": _read_lines("was-01-catalina.log"),
        }
    return {
        "agent_name": "DB-01",
        "role": "DB",
        "status": "warning",
        "host": "DB-01",
        "service": "PostgreSQL",
        "metrics": {"cpu": "66%", "memory": "73%", "active_sessions": 187, "lock_wait_count": 14},
        "logs": _read_lines("db-01-postgres.log"),
    }


async def collect_agent_logs() -> list[dict[str, Any]]:
    """Collect logs from external mock agents if configured; fallback to internal mock payloads."""
    settings = get_settings()
    targets = [
        ("WEB", settings.agent_web_url),
        ("WAS", settings.agent_was_url),
        ("DB", settings.agent_db_url),
    ]
    results: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=8.0) as client:
        for role, base_url in targets:
            if base_url:
                try:
                    response = await client.get(f"{base_url.rstrip('/')}/logs")
                    response.raise_for_status()
                    payload = response.json()
                    payload["collection_mode"] = "external-mock-agent"
                    results.append(payload)
                    continue
                except Exception as exc:
                    payload = internal_agent_payload(role)
                    payload["collection_mode"] = "internal-fallback"
                    payload["collection_error"] = str(exc)
                    results.append(payload)
                    continue
            payload = internal_agent_payload(role)
            payload["collection_mode"] = "internal-mock-agent"
            results.append(payload)
    return results
