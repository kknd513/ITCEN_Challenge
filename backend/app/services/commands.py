from __future__ import annotations

from typing import Any

BLOCKED_KEYWORDS = [
    "rm", "mv", "cp", "chmod", "chown", "kill", "shutdown", "reboot", "init", "systemctl restart",
    "service restart", "vi", "vim", "nano", "dd", "mkfs", "fdisk", "truncate", ">", ">>", "sudo",
]

COMMAND_RULES = [
    {
        "keywords": ["web", "nginx", "502", "upstream", "오류", "로그"],
        "target": "WEB-01",
        "command": "tail -n 100 /var/log/nginx/error.log | grep -Ei 'upstream|502|timeout|error'",
        "description": "WEB-01 Nginx 502 및 upstream timeout 로그 조회",
    },
    {
        "keywords": ["was", "tomcat", "catalina", "쓰레드", "thread", "로그"],
        "target": "WAS-01",
        "command": "tail -n 150 /app/tomcat/logs/catalina.out | grep -Ei 'HikariPool|SocketTimeout|SEVERE|Exception'",
        "description": "WAS-01 Tomcat 장애 로그 조회",
    },
    {
        "keywords": ["db", "postgres", "connection", "세션", "5432"],
        "target": "DB-01",
        "command": "ss -tnp | grep ':5432' | head -n 50",
        "description": "DB 연결 상태 조회",
    },
    {
        "keywords": ["프로세스", "process", "tomcat", "java", "상태"],
        "target": "WAS-01",
        "command": "ps -ef | grep -E 'tomcat|java' | grep -v grep",
        "description": "Tomcat/Java 프로세스 조회",
    },
    {
        "keywords": ["디스크", "disk", "용량", "filesystem"],
        "target": "ALL",
        "command": "df -h",
        "description": "파일시스템 사용률 조회",
    },
    {
        "keywords": ["메모리", "memory", "mem"],
        "target": "ALL",
        "command": "free -m",
        "description": "메모리 사용률 조회",
    },
]


def is_safe_command(command: str) -> bool:
    lower = command.lower()
    return not any(keyword in lower for keyword in BLOCKED_KEYWORDS)


def map_command(query: str, target: str | None = None) -> list[dict[str, Any]]:
    lower = query.lower()
    suggestions: list[dict[str, Any]] = []
    for rule in COMMAND_RULES:
        if target and rule["target"] not in {target, "ALL"}:
            continue
        if any(keyword.lower() in lower for keyword in rule["keywords"]):
            suggestions.append({
                "target": rule["target"],
                "command": rule["command"],
                "description": rule["description"],
                "safe": is_safe_command(rule["command"]),
                "mode": "read-only",
            })
    if not suggestions:
        suggestions.append({
            "target": target or "ALL",
            "command": "tail -n 100 /var/log/messages",
            "description": "기본 시스템 로그 조회",
            "safe": True,
            "mode": "read-only",
        })
    return suggestions
