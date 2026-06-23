import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "linux_command_catalog.json"
SERVER_ALIASES = {
    "A": "server-a", "A서버": "server-a", "WEB": "server-a", "WEB서버": "server-a",
    "B": "server-b", "B서버": "server-b", "WAS": "server-b", "WAS서버": "server-b",
    "C": "server-c", "C서버": "server-c", "DB": "server-c", "DB서버": "server-c",
}
KEYWORD_MAP = {
    "disk_usage": ["디스크", "용량", "df", "파티션"],
    "memory_usage": ["메모리", "memory", "free", "ram"],
    "cpu_load": ["cpu", "부하", "로드", "uptime", "load"],
    "top_processes": ["프로세스", "process", "ps", "많이 쓰", "상위"],
    "network_ports": ["포트", "listen", "리스닝", "ss", "소켓"],
    "ip_address": ["ip", "주소", "인터페이스", "네트워크"],
    "recent_syslog": ["로그", "syslog", "journal", "에러", "오류"],
    "failed_services": ["서비스", "failed", "실패", "장애 서비스"],
}


def load_catalog() -> List[Dict[str, Any]]:
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_target_server(question: str) -> str:
    text = question.upper().replace(" ", "")
    for alias, server_id in SERVER_ALIASES.items():
        if alias.upper().replace(" ", "") in text:
            return server_id
    return os.getenv("CENOPS_DEFAULT_SERVER", "server-a")


def map_question_to_command(question: str) -> Dict[str, Any]:
    q = question.lower()
    catalog = load_catalog()
    best_intent = None
    best_score = 0
    for intent, keywords in KEYWORD_MAP.items():
        score = sum(1 for kw in keywords if kw.lower() in q)
        if score > best_score:
            best_score = score
            best_intent = intent
    if not best_intent:
        raise ValueError("지원하지 않는 질의입니다. 예: A서버 디스크 사용량 확인, B서버 열린 포트 확인")
    item = next(x for x in catalog if x["intent"] == best_intent)
    return {
        "server_id": resolve_target_server(question),
        "intent": item["intent"],
        "command": item["command_template"],
        "risk": item["risk"],
        "description": item["description"],
        "confidence": min(0.95, 0.55 + best_score * 0.15),
    }
