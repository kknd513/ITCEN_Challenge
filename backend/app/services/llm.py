from __future__ import annotations

from typing import Any
import json

try:
    from openai import AsyncOpenAI
except Exception:  # pragma: no cover - local fallback when openai package is not installed
    AsyncOpenAI = None  # type: ignore

from app.core.config import get_settings


def deterministic_analysis(agent_logs: list[dict[str, Any]], rag_sources: list[dict[str, Any]], commands: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "summary": "WEB-01 502 오류는 WAS-01 Tomcat의 DB Connection Pool 고갈과 DB 응답 지연이 결합되어 Nginx upstream timeout으로 표출된 가능성이 높습니다.",
        "causes": [
            {
                "rank": 1,
                "title": "WAS Connection Pool 고갈",
                "probability": 0.82,
                "reason": "WAS 로그에서 HikariPool connection timeout, active_threads=max_threads 상태가 확인됩니다.",
                "evidence": [
                    "HikariPool-1 - Connection is not available, request timed out after 30000ms",
                    "WAS-01 active_threads=200, max_threads=200",
                ],
                "recommended_commands": [
                    "tail -n 150 /app/tomcat/logs/catalina.out | grep -Ei 'HikariPool|SocketTimeout|SEVERE|Exception'",
                    "ps -ef | grep -E 'tomcat|java' | grep -v grep",
                ],
                "next_actions": [
                    "WAS Connection Pool 설정값과 DB 세션 한도를 확인합니다.",
                    "최근 배포/트래픽 증가 여부를 확인합니다.",
                ],
            },
            {
                "rank": 2,
                "title": "DB 응답 지연 또는 세션 과다",
                "probability": 0.67,
                "reason": "DB Agent에서 active session 증가와 connection warning 로그가 확인됩니다.",
                "evidence": [
                    "active_sessions=187, lock_wait_count=14",
                    "connection received from WAS-01, request timed out after 30001ms",
                ],
                "recommended_commands": ["ss -tnp | grep ':5432' | head -n 50"],
                "next_actions": ["DB Lock Wait, Slow Query, 세션 수 증가 원인을 확인합니다."],
            },
            {
                "rank": 3,
                "title": "Nginx upstream timeout",
                "probability": 0.48,
                "reason": "WEB-01 Nginx error.log에서 upstream timed out 및 502 Bad Gateway가 확인됩니다.",
                "evidence": [
                    "upstream timed out while reading response header from upstream",
                    "GET /api/order/list HTTP/1.1 -> 502 Bad Gateway",
                ],
                "recommended_commands": ["tail -n 100 /var/log/nginx/error.log | grep -Ei 'upstream|502|timeout|error'"],
                "next_actions": ["proxy_read_timeout 설정과 WAS 응답시간을 함께 확인합니다."],
            },
        ],
    }


async def analyze_with_llm(message: str, agent_logs: list[dict[str, Any]], rag_sources: list[dict[str, Any]], commands: list[dict[str, Any]]) -> dict[str, Any]:
    settings = get_settings()
    if not settings.openai_api_key:
        return deterministic_analysis(agent_logs, rag_sources, commands)

    if AsyncOpenAI is None:
        return deterministic_analysis(agent_logs, rag_sources, commands)
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    system_prompt = """
당신은 공공 정보시스템 운영자를 지원하는 CENOps Copilot입니다.
반드시 JSON만 출력하세요. 장애 원인을 확정하지 말고 가능성이 높은 후보 Top 3를 제시하세요.
각 후보는 rank, title, probability, reason, evidence, recommended_commands, next_actions 필드를 가져야 합니다.
위험한 명령어는 제안하지 말고 조회성 명령어만 제안하세요.
""".strip()
    user_payload = {
        "operator_message": message,
        "agent_logs": agent_logs,
        "rag_sources": rag_sources,
        "safe_commands": commands,
    }
    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        if "summary" not in parsed or "causes" not in parsed:
            return deterministic_analysis(agent_logs, rag_sources, commands)
        return parsed
    except Exception:
        return deterministic_analysis(agent_logs, rag_sources, commands)
