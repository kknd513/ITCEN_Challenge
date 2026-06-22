from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


def build_report(incident_id: str, input_text: str, analysis: dict[str, Any], rag_sources: list[dict[str, Any]], agent_logs: list[dict[str, Any]]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines: list[str] = []
    lines.append(f"# CENOps Copilot 장애 분석 보고서")
    lines.append("")
    lines.append(f"- 보고서 생성시각: {now}")
    lines.append(f"- Incident ID: {incident_id}")
    lines.append(f"- 입력 문구: {input_text}")
    lines.append(f"- 장애 유형: Web/WAS 502 Bad Gateway")
    lines.append(f"- 영향 시스템: WEB-01, WAS-01, DB-01")
    lines.append("")
    lines.append("## 1. 장애 요약")
    lines.append(analysis.get("summary", "분석 요약 없음"))
    lines.append("")
    lines.append("## 2. 원인 후보 Top 3")
    for cause in analysis.get("causes", []):
        lines.append(f"### {cause.get('rank')}. {cause.get('title')} (가능성 {cause.get('probability')})")
        lines.append(f"- 판단 근거: {cause.get('reason')}")
        lines.append("- 근거 로그:")
        for item in cause.get("evidence", []):
            lines.append(f"  - `{item}`")
        lines.append("- 권장 조회 명령어:")
        for cmd in cause.get("recommended_commands", []):
            lines.append(f"  - `{cmd}`")
        lines.append("- 다음 조치:")
        for action in cause.get("next_actions", []):
            lines.append(f"  - {action}")
        lines.append("")
    lines.append("## 3. 수집 Agent 요약")
    for agent in agent_logs:
        lines.append(f"- {agent.get('agent_name')} / {agent.get('role')} / 상태: {agent.get('status')} / 수집방식: {agent.get('collection_mode', 'unknown')}")
    lines.append("")
    lines.append("## 4. 참조 RAG 문서")
    for source in rag_sources:
        lines.append(f"- {source.get('title')} ({source.get('path')}) / score={source.get('score')}")
    lines.append("")
    lines.append("## 5. 운영자 확인 사항")
    lines.append("- 본 보고서는 원인 후보를 우선순위로 제시하며 최종 장애 원인 확정은 운영자 검토가 필요합니다.")
    lines.append("- 제안된 Command는 조회성 명령어로 제한되어 있으며, 변경·삭제·재시작 명령은 수행하지 않습니다.")
    return "\n".join(lines)
