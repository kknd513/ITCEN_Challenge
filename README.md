# CENOps Copilot Railway Prototype

Railway 권장 구성안 기반 CENOps Copilot 프로토타입 소스입니다.

## 핵심 기능

- Web/WAS 502 장애 시나리오 분석
- Zenius 알림 문구 입력 → Agent 3대 로그 검색 → RAG 운영문서 검색 → 원인 후보 Top 3 제시
- 운영문서 RAG 검색
- Mock Agent 상태 수집
- 실제 A~C 서버 Agent 질의
- 실제 A~C 서버 Agent 로컬 문서 RAG 질의
- 조회성 자연어 Command 제안
- 장애 보고서 Markdown 생성

## 서비스 구성

```text
/frontend      React + Vite UI
/backend       FastAPI Orchestrator
/mock-agent    Railway Mock Agent 서비스
/real-agent    실제 A~C 서버 설치용 Agent
/db            PostgreSQL + pgvector Schema
/docs          Railway 배포 통합 매뉴얼
/scripts       API 테스트 스크립트
```

## 실서버 매핑

```text
A-SERVER = WEB-01 = Nginx / Web 계층
B-SERVER = WAS-01 = Tomcat / WAS 계층
C-SERVER = DB-01 = PostgreSQL / DB 계층
```

## 빠른 로컬 실행

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### API 테스트

```bash
BASE_URL=http://localhost:8000 ./scripts/test_backend.sh
```

## Railway 배포

자세한 절차는 아래 단일 문서를 참조하십시오.

```text
docs/RAILWAY_DEPLOYMENT_GUIDE.md
```

## 주요 API

```text
GET  /health
GET  /api/servers
POST /api/chat
POST /api/incident/analyze
POST /api/servers/query
POST /api/server-rag/query
POST /api/rag/search
POST /api/command/map
POST /api/report/generate
```

## 실서버 Agent 연동 환경변수

Backend:

```text
SERVER_A_AGENT_URL=http://<A-SERVER-IP>:8080
SERVER_B_AGENT_URL=http://<B-SERVER-IP>:8080
SERVER_C_AGENT_URL=http://<C-SERVER-IP>:8080
SERVER_AGENT_TOKEN=change-me-agent-token
```

Real Agent:

```text
AGENT_NAME=A-SERVER
AGENT_ROLE=WEB
AGENT_TOKEN=change-me-agent-token
LOG_PATHS=/var/log/nginx/error.log,/var/log/messages,/var/log/syslog
DOCS_DIR=/app/docs
```

## 보안 제한

- 조회성 명령과 로그/문서 검색만 수행합니다.
- 파일 삭제, 수정, 서비스 재시작, 권한 변경 명령은 수행하지 않습니다.
- 공모전/제안서용 MVP이므로 운영망 적용 시 인증, 암호화, 감사로그, 망분리 구조 보강이 필요합니다.
