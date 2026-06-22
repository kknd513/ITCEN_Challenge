from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., description="운영자 입력 메시지")
    target: str | None = Field(default=None, description="선택 대상 서버: A, B, C, WEB-01, WAS-01, DB-01")


class RagSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    target: str | None = Field(default=None, description="선택 대상 서버 또는 문서 범위")


class CommandMapRequest(BaseModel):
    query: str
    target: str | None = None


class ServerQueryRequest(BaseModel):
    message: str
    target: str | None = Field(default=None, description="A/B/C 또는 WEB-01/WAS-01/DB-01. 미지정 시 문구에서 자동 추론")
    include_rag: bool = True


class ServerRagRequest(BaseModel):
    query: str
    target: str | None = Field(default=None, description="A/B/C 또는 WEB-01/WAS-01/DB-01. 미지정 시 전체 검색")
    top_k: int = 5
    include_agent_local_docs: bool = True


class ReportGenerateRequest(BaseModel):
    incident_id: str


class CauseCandidate(BaseModel):
    rank: int
    title: str
    probability: float
    reason: str
    evidence: list[str]
    recommended_commands: list[str]
    next_actions: list[str]


class AnalysisResponse(BaseModel):
    incident_id: str
    incident_type: str
    summary: str
    causes: list[CauseCandidate] = []
    agent_logs: list[dict[str, Any]] = []
    rag_sources: list[dict[str, Any]] = []
    command_suggestions: list[dict[str, Any]] = []
    report_markdown: str = ""
