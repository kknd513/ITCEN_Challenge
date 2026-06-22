#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"

echo "[1] Health"
curl -s "$BASE_URL/health" | python3 -m json.tool || true

echo "\n[2] Server list"
curl -s "$BASE_URL/api/servers" | python3 -m json.tool || true

echo "\n[3] Web/WAS 502 incident analysis"
curl -s -X POST "$BASE_URL/api/chat" \
  -H 'Content-Type: application/json' \
  -d '{"message":"Zenius 알림: WEB-01 502 오류 발생. 원인 분석해줘."}' | python3 -m json.tool || true

echo "\n[4] A server real/mocked query"
curl -s -X POST "$BASE_URL/api/chat" \
  -H 'Content-Type: application/json' \
  -d '{"message":"A서버 최근 Nginx 502 오류 로그 확인해줘","target":"A"}' | python3 -m json.tool || true

echo "\n[5] B server RAG query"
curl -s -X POST "$BASE_URL/api/server-rag/query" \
  -H 'Content-Type: application/json' \
  -d '{"query":"B서버 Tomcat 502 HikariPool timeout 조치 절차 알려줘","target":"B","top_k":5,"include_agent_local_docs":true}' | python3 -m json.tool || true
