from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import httpx

from app.core.config import get_settings
from app.services.mock_agents import internal_agent_payload
from app.services.rag import rag_service
from app.services.commands import map_command


@dataclass(frozen=True)
class ServerTarget:
    key: str
    label: str
    role: str
    host_alias: str
    url: str | None


def get_server_targets() -> dict[str, ServerTarget]:
    settings = get_settings()
    a = ServerTarget("A", "A-SERVER / WEB-01", "WEB", "WEB-01", settings.server_a_agent_url)
    b = ServerTarget("B", "B-SERVER / WAS-01", "WAS", "WAS-01", settings.server_b_agent_url)
    c = ServerTarget("C", "C-SERVER / DB-01", "DB", "DB-01", settings.server_c_agent_url)
    return {
        "A": a, "A서버": a, "SERVER-A": a, "WEB": a, "WEB-01": a, "웹": a,
        "B": b, "B서버": b, "SERVER-B": b, "WAS": b, "WAS-01": b, "톰캣": b, "TOMCAT": b,
        "C": c, "C서버": c, "SERVER-C": c, "DB": c, "DB-01": c, "DBMS": c, "POSTGRES": c, "POSTGRESQL": c,
    }


def unique_targets(targets: list[ServerTarget]) -> list[ServerTarget]:
    seen: set[str] = set()
    result: list[ServerTarget] = []
    for target in targets:
        if target.key in seen:
            continue
        seen.add(target.key)
        result.append(target)
    return result


def detect_targets(message: str, target: str | None = None) -> list[ServerTarget]:
    mapping = get_server_targets()
    if target:
        selected = mapping.get(target.upper()) or mapping.get(target) or mapping.get(target.replace(" ", ""))
        if selected:
            return [selected]

    upper = message.upper().replace(" ", "")
    found: list[ServerTarget] = []
    for alias, server in mapping.items():
        if alias.upper().replace(" ", "") in upper:
            found.append(server)

    if found:
        return unique_targets(found)

    # If no explicit server is named, use all 3 servers for the incident analysis workflow.
    base = get_server_targets()
    return unique_targets([base["A"], base["B"], base["C"]])


def is_server_query(message: str) -> bool:
    lower = message.lower()
    keywords = [
        "a서버", "b서버", "c서버", "web-01", "was-01", "db-01",
        "서버", "로그", "상태", "프로세스", "명령", "command", "tail", "df", "ps", "ss",
    ]
    return any(k in lower for k in keywords)


def is_rag_question(message: str) -> bool:
    lower = message.lower()
    keywords = ["문서", "rag", "조치", "가이드", "산출물", "매뉴얼", "절차", "tomcat", "502"]
    return any(k in lower for k in keywords)


async def query_one_server(server: ServerTarget, message: str) -> dict[str, Any]:
    settings = get_settings()
    headers: dict[str, str] = {}
    if settings.server_agent_token:
        headers["Authorization"] = f"Bearer {settings.server_agent_token}"

    if server.url:
        try:
            async with httpx.AsyncClient(timeout=settings.server_query_timeout) as client:
                response = await client.post(
                    f"{server.url.rstrip('/')}/query",
                    json={"message": message, "target": server.key},
                    headers=headers,
                )
                response.raise_for_status()
                payload = response.json()
                payload.setdefault("agent_name", server.host_alias)
                payload.setdefault("role", server.role)
                payload["collection_mode"] = "real-agent"
                payload["server_key"] = server.key
                payload["server_label"] = server.label
                return payload
        except Exception as exc:
            payload = internal_agent_payload(server.role)
            payload["collection_mode"] = "real-agent-fallback-mock"
            payload["collection_error"] = str(exc)
            payload["server_key"] = server.key
            payload["server_label"] = server.label
            return payload

    payload = internal_agent_payload(server.role)
    payload["collection_mode"] = "mock-no-real-agent-url"
    payload["server_key"] = server.key
    payload["server_label"] = server.label
    return payload


async def query_servers(message: str, target: str | None = None) -> list[dict[str, Any]]:
    targets = detect_targets(message, target)
    results: list[dict[str, Any]] = []
    for server in targets:
        results.append(await query_one_server(server, message))
    return results


async def query_one_server_rag(server: ServerTarget, query: str, top_k: int = 5) -> list[dict[str, Any]]:
    settings = get_settings()
    headers: dict[str, str] = {}
    if settings.server_agent_token:
        headers["Authorization"] = f"Bearer {settings.server_agent_token}"

    if not server.url:
        return []

    try:
        async with httpx.AsyncClient(timeout=settings.server_query_timeout) as client:
            response = await client.post(
                f"{server.url.rstrip('/')}/rag/search",
                json={"query": query, "top_k": top_k},
                headers=headers,
            )
            response.raise_for_status()
            docs = response.json().get("results", [])
            for doc in docs:
                doc["source_type"] = "agent-local-rag-document"
                doc["server_key"] = server.key
                doc["server_label"] = server.label
            return docs
    except Exception as exc:
        return [{
            "title": "Agent local RAG query failed",
            "source_type": "agent-local-rag-error",
            "path": server.url,
            "score": 0,
            "content": str(exc),
            "server_key": server.key,
            "server_label": server.label,
        }]


async def query_server_rag(query: str, target: str | None = None, top_k: int = 5, include_agent_local_docs: bool = True) -> list[dict[str, Any]]:
    # Backend RAG is always searched. It represents the central CENOps Copilot knowledge base.
    central_query = query
    if target:
        central_query = f"{target} {query}"
    central_results = rag_service.search(central_query, top_k=top_k)
    for result in central_results:
        result.setdefault("source_type", "central-rag-document")

    if not include_agent_local_docs:
        return central_results

    agent_docs: list[dict[str, Any]] = []
    targets = detect_targets(query, target)
    for server in targets:
        agent_docs.extend(await query_one_server_rag(server, query, top_k=max(1, top_k // 2)))

    return (central_results + agent_docs)[: max(top_k, len(central_results)) + len(agent_docs)]


def build_server_question_summary(message: str, agent_payloads: list[dict[str, Any]], rag_sources: list[dict[str, Any]] | None = None) -> str:
    lines: list[str] = []
    lines.append("요청하신 서버 질의 결과입니다.")
    for payload in agent_payloads:
        name = payload.get("server_label") or payload.get("agent_name")
        status = payload.get("status", "unknown")
        mode = payload.get("collection_mode", "unknown")
        metrics = payload.get("metrics", {})
        logs = payload.get("logs", [])
        lines.append(f"- {name}: 상태={status}, 수집방식={mode}, 주요지표={metrics}")
        if logs:
            lines.append(f"  - 최근 로그 예시: {str(logs[0])[:180]}")
    if rag_sources:
        titles = ", ".join([str(s.get("title")) for s in rag_sources[:3]])
        lines.append(f"- 참조 문서: {titles}")
    lines.append("- 주의: 변경·삭제·재시작 명령은 자동 수행하지 않으며 조회성 정보만 제공합니다.")
    return "\n".join(lines)
