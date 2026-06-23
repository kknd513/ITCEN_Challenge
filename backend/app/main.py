from __future__ import annotations

from uuid import uuid4
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import natural_command


from app.core.config import get_settings
from app.models.schemas import (
    ChatRequest,
    RagSearchRequest,
    CommandMapRequest,
    ServerQueryRequest,
    ServerRagRequest,
    AnalysisResponse,
)
from app.services.mock_agents import collect_agent_logs, internal_agent_payload
from app.services.rag import rag_service
from app.services.commands import map_command
from app.services.llm import analyze_with_llm
from app.services.report import build_report
from app.services.storage import save_incident, save_analysis, save_report, save_agent_logs
from app.services.real_agents import (
    get_server_targets,
    query_servers,
    query_server_rag,
    is_server_query,
    is_rag_question,
    build_server_question_summary,
)

settings = get_settings()

app = FastAPI(
    title="CENOps Copilot Backend",
    version="0.2.0",
    description="Railway prototype for Web/WAS 502 incident analysis, real A~C server query, and RAG Q&A",
)

origins = [settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173", "*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(natural_command.router)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "cenops-copilot-backend"}


@app.get("/api/servers")
async def servers() -> dict[str, Any]:
    base = get_server_targets()
    servers = []
    for key in ["A", "B", "C"]:
        target = base[key]
        servers.append({
            "key": target.key,
            "label": target.label,
            "role": target.role,
            "host_alias": target.host_alias,
            "mode": "real-agent" if target.url else "mock-fallback",
            "url_configured": bool(target.url),
        })
    return {"servers": servers}


@app.get("/api/mock-agent/{agent}/logs")
async def mock_agent_logs(agent: str) -> dict[str, Any]:
    return internal_agent_payload(agent)


@app.post("/api/rag/search")
async def rag_search(request: RagSearchRequest) -> dict[str, Any]:
    return {"query": request.query, "target": request.target, "results": rag_service.search(request.query, top_k=request.top_k)}


@app.post("/api/server-rag/query")
async def server_rag_query(request: ServerRagRequest) -> dict[str, Any]:
    results = await query_server_rag(
        query=request.query,
        target=request.target,
        top_k=request.top_k,
        include_agent_local_docs=request.include_agent_local_docs,
    )
    return {"query": request.query, "target": request.target, "results": results}


@app.post("/api/command/map")
async def command_map(request: CommandMapRequest) -> dict[str, Any]:
    return {"query": request.query, "commands": map_command(request.query, request.target)}


@app.post("/api/servers/query", response_model=AnalysisResponse)
async def server_query(request: ServerQueryRequest) -> AnalysisResponse:
    incident_id = str(uuid4())
    agent_payloads = await query_servers(request.message, request.target)
    rag_sources = []
    if request.include_rag:
        rag_sources = await query_server_rag(request.message, request.target, top_k=5, include_agent_local_docs=True)
    command_suggestions = map_command(request.message, request.target)
    save_incident(incident_id, request.message, "server_query")
    save_agent_logs(incident_id, agent_payloads)
    summary = build_server_question_summary(request.message, agent_payloads, rag_sources)
    report_markdown = build_report(incident_id, request.message, {"summary": summary, "causes": []}, rag_sources, agent_payloads)
    return AnalysisResponse(
        incident_id=incident_id,
        incident_type="server_query",
        summary=summary,
        causes=[],
        agent_logs=agent_payloads,
        rag_sources=rag_sources,
        command_suggestions=command_suggestions,
        report_markdown=report_markdown,
    )


@app.post("/api/incident/analyze", response_model=AnalysisResponse)
async def analyze_incident(request: ChatRequest) -> AnalysisResponse:
    incident_id = str(uuid4())
    incident_type = "web_was_502"
    save_incident(incident_id, request.message, incident_type)

    # Web/WAS/DB 502 시나리오는 Railway Mock Agent 또는 실제 A~C Agent 중 설정 가능한 쪽을 사용합니다.
    # SERVER_A/B/C_AGENT_URL이 설정되어 있으면 실서버 Agent를 우선 조회합니다.
    if settings.server_a_agent_url or settings.server_b_agent_url or settings.server_c_agent_url:
        agent_logs = await query_servers(request.message, request.target)
    else:
        agent_logs = await collect_agent_logs()

    rag_query = f"{request.message} Tomcat HikariPool Nginx upstream timeout Web WAS DB 502 A서버 B서버 C서버"
    rag_sources = await query_server_rag(rag_query, request.target, top_k=5, include_agent_local_docs=True)
    command_suggestions = map_command(request.message + " 502 tomcat nginx db connection", request.target)
    analysis = await analyze_with_llm(request.message, agent_logs, rag_sources, command_suggestions)
    report_markdown = build_report(incident_id, request.message, analysis, rag_sources, agent_logs)
    report_id = str(uuid4())
    save_analysis(incident_id, analysis)
    save_agent_logs(incident_id, agent_logs)
    save_report(report_id, incident_id, "Web/WAS 502 장애 분석 보고서", report_markdown)

    return AnalysisResponse(
        incident_id=incident_id,
        incident_type=incident_type,
        summary=analysis.get("summary", ""),
        causes=analysis.get("causes", []),
        agent_logs=agent_logs,
        rag_sources=rag_sources,
        command_suggestions=command_suggestions,
        report_markdown=report_markdown,
    )


@app.post("/api/chat", response_model=AnalysisResponse)
async def chat(request: ChatRequest) -> AnalysisResponse:
    message = request.message.lower()

    explicit_rag_terms = ["문서", "매뉴얼", "가이드", "절차", "산출물", "runbook", "찾아줘", "알려줘"]
    explicit_server_terms = ["로그", "상태", "프로세스", "세션", "명령", "command", "확인"]
    incident_terms = ["zenius", "bad gateway", "장애", "원인 분석", "장애 분석"]

    # 1) 명시적 RAG 문서 질의: 중앙 RAG + 선택 시 A~C 서버 로컬 문서 검색
    if is_rag_question(request.message) and any(term in message for term in explicit_rag_terms):
        incident_id = str(uuid4())
        rag_sources = await query_server_rag(request.message, request.target, top_k=6, include_agent_local_docs=True)
        command_suggestions = map_command(request.message, request.target)
        summary = "RAG 검색 결과를 기준으로 답변합니다.\n" + "\n".join([
            f"- {source.get('title')} ({source.get('path')}): {str(source.get('content', ''))[:220]}"
            for source in rag_sources[:4]
        ])
        report_markdown = build_report(incident_id, request.message, {"summary": summary, "causes": []}, rag_sources, [])
        return AnalysisResponse(
            incident_id=incident_id,
            incident_type="rag_question",
            summary=summary,
            causes=[],
            agent_logs=[],
            rag_sources=rag_sources,
            command_suggestions=command_suggestions,
            report_markdown=report_markdown,
        )

    # 2) 실제 A~C 서버 상태/로그/조회성 명령 질의
    # 예: "A서버 최근 Nginx 502 오류 로그 확인해줘"
    if is_server_query(request.message) and any(term in message for term in explicit_server_terms) and "원인 분석" not in message and "장애 분석" not in message:
        return await server_query(ServerQueryRequest(message=request.message, target=request.target, include_rag=True))

    # 3) Web/WAS 502 장애 분석
    if any(keyword in message for keyword in incident_terms) or ("502" in message and ("원인" in message or "장애" in message)):
        return await analyze_incident(request)

    # Default: treat as server/RAG support question to avoid empty chatbot result.
    return await server_query(ServerQueryRequest(message=request.message, target=request.target, include_rag=True))


@app.post("/api/report/generate")
async def report_generate(request: ChatRequest) -> AnalysisResponse:
    return await analyze_incident(request)
