from __future__ import annotations

import os
from fastapi import FastAPI

app = FastAPI(title="CENOps Mock Agent", version="0.1.0")


def payload_for_role(role: str) -> dict:
    role = role.upper()
    if role == "WAS":
        return {
            "agent_name": os.getenv("AGENT_NAME", "WAS-01"),
            "role": "WAS",
            "status": "critical",
            "service": "Tomcat",
            "metrics": {"cpu": "78%", "memory": "82%", "active_threads": 200, "max_threads": 200},
            "logs": [
                "2026-06-22 10:23:38 ERROR HikariPool-1 - Connection is not available, request timed out after 30000ms",
                "2026-06-22 10:23:39 java.sql.SQLTransientConnectionException",
                "2026-06-22 10:23:40 WARN Active threads=200, maxThreads=200",
            ],
        }
    if role == "DB":
        return {
            "agent_name": os.getenv("AGENT_NAME", "DB-01"),
            "role": "DB",
            "status": "warning",
            "service": "PostgreSQL",
            "metrics": {"cpu": "66%", "memory": "73%", "active_sessions": 187, "lock_wait_count": 14},
            "logs": [
                "2026-06-22 10:23:36 LOG duration: 382000.231 ms statement: SELECT * FROM orders",
                "2026-06-22 10:23:37 WARNING lock wait detected for relation orders",
                "2026-06-22 10:23:40 LOG active_sessions=187 lock_wait_count=14 slow_query_count=32",
            ],
        }
    return {
        "agent_name": os.getenv("AGENT_NAME", "WEB-01"),
        "role": "WEB",
        "status": "warning",
        "service": "Nginx Reverse Proxy",
        "metrics": {"cpu": "35%", "memory": "46%", "active_connections": 382, "upstream_5xx": 27},
        "logs": [
            "2026-06-22 10:23:41 [error] upstream timed out while reading response header from upstream",
            "2026-06-22 10:23:45 [warn] upstream server temporarily disabled",
            "2026-06-22 10:23:48 access: GET /api/order/list HTTP/1.1 -> 502 Bad Gateway",
        ],
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "agent_role": os.getenv("AGENT_ROLE", "WEB")}


@app.get("/logs")
def logs() -> dict:
    return payload_for_role(os.getenv("AGENT_ROLE", "WEB"))
