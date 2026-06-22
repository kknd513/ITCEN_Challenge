from __future__ import annotations

from pathlib import Path
from typing import Any
import os
import re
import socket
import subprocess

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

AGENT_NAME = os.getenv("AGENT_NAME", "A-SERVER")
AGENT_ROLE = os.getenv("AGENT_ROLE", "WEB")
AGENT_TOKEN = os.getenv("AGENT_TOKEN")
LOG_PATHS = [p.strip() for p in os.getenv("LOG_PATHS", "/var/log/messages,/var/log/syslog").split(",") if p.strip()]
DOCS_DIR = Path(os.getenv("DOCS_DIR", "/app/docs"))
MAX_LOG_LINES = int(os.getenv("MAX_LOG_LINES", "120"))

app = FastAPI(title="CENOps Real Server Agent", version="0.1.0")


class QueryRequest(BaseModel):
    message: str
    target: str | None = None


class RagSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


def require_token(authorization: str | None) -> None:
    if not AGENT_TOKEN:
        return
    expected = f"Bearer {AGENT_TOKEN}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="invalid agent token")


def run_readonly_command(args: list[str], timeout: int = 5) -> dict[str, Any]:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        return {
            "command": " ".join(args),
            "returncode": result.returncode,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-1000:],
        }
    except Exception as exc:
        return {"command": " ".join(args), "returncode": -1, "stdout": "", "stderr": str(exc)}


def tail_file(path: str, max_lines: int = MAX_LOG_LINES) -> list[str]:
    p = Path(path)
    if not p.exists() or not p.is_file():
        return [f"[WARN] log file not found: {path}"]
    try:
        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        return lines[-max_lines:]
    except Exception as exc:
        return [f"[ERROR] failed to read {path}: {exc}"]


def filter_logs(message: str) -> list[str]:
    lower = message.lower()
    patterns = ["error", "warn", "exception", "timeout", "502", "hikaripool", "upstream", "connection", "failed", "severe"]
    if "tomcat" in lower or "was" in lower:
        patterns.extend(["catalina", "servlet", "sockettimeoutexception", "thread"])
    if "db" in lower or "postgres" in lower:
        patterns.extend(["postgres", "5432", "lock", "session"])
    compiled = re.compile("|".join(re.escape(p) for p in patterns), re.IGNORECASE)
    selected: list[str] = []
    for path in LOG_PATHS:
        for line in tail_file(path):
            if compiled.search(line):
                selected.append(f"{path}: {line}")
    return selected[:MAX_LOG_LINES]


def collect_metrics() -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "hostname": socket.gethostname(),
        "agent_name": AGENT_NAME,
        "agent_role": AGENT_ROLE,
    }
    for key, cmd in {
        "uptime": ["uptime"],
        "disk": ["df", "-h"],
        "memory": ["free", "-m"],
        "process": ["ps", "-eo", "pid,ppid,comm,%cpu,%mem", "--sort=-%cpu"],
    }.items():
        output = run_readonly_command(cmd)
        metrics[key] = output.get("stdout", "")[:2000]
    # ss may not exist in minimal containers, so it is optional.
    metrics["connections"] = run_readonly_command(["sh", "-c", "command -v ss >/dev/null 2>&1 && ss -tnp | head -n 80 || true"]).get("stdout", "")[:2000]
    return metrics


def normalize(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z0-9가-힣_.:/-]+", text.lower()))


def search_local_docs(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    if not DOCS_DIR.exists():
        return []
    q = normalize(query)
    scored: list[tuple[int, Path, str]] = []
    for path in DOCS_DIR.glob("**/*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".log"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        score = len(q & normalize(text + " " + path.name))
        if score > 0:
            scored.append((score, path, text[:1200]))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "title": path.stem,
            "path": str(path),
            "score": score,
            "content": content,
            "source_type": "agent-local-document",
            "agent_name": AGENT_NAME,
        }
        for score, path, content in scored[:top_k]
    ]


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "agent_name": AGENT_NAME, "agent_role": AGENT_ROLE, "hostname": socket.gethostname()}


@app.post("/query")
async def query(request: QueryRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    logs = filter_logs(request.message)
    metrics = collect_metrics()
    docs = search_local_docs(request.message, top_k=3)
    status = "critical" if any("502" in line or "Exception" in line or "timeout" in line.lower() for line in logs) else "normal"
    return {
        "agent_name": AGENT_NAME,
        "role": AGENT_ROLE,
        "host": socket.gethostname(),
        "status": status,
        "message": request.message,
        "metrics": metrics,
        "logs": logs,
        "local_rag_sources": docs,
        "allowed_mode": "read-only",
    }


@app.post("/rag/search")
async def rag_search(request: RagSearchRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    return {"query": request.query, "results": search_local_docs(request.query, top_k=request.top_k)}
