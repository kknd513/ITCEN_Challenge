# CENOps Copilot Railway 배포 통합 매뉴얼

본 문서는 CENOps Copilot 프로토타입을 Railway 환경에 배포하고, Web/WAS 502 장애 시나리오를 End-to-End로 검증하기 위한 단일 배포 가이드입니다.

구성 목표는 다음과 같습니다.

1. Railway에서 Frontend, Backend, PostgreSQL+pgvector, Mock Agent 또는 실제 A~C 서버 Agent를 구성한다.
2. 운영자가 챗봇에 Zenius 알림 문구를 입력하면 Backend가 Agent 3대의 로그와 상태를 수집한다.
3. Backend가 중앙 RAG 문서와, 선택 시 A~C 서버 로컬 문서를 검색한다.
4. OpenAI API를 활용해 원인 후보 Top 3, 근거 로그, 조회성 Command, 장애 보고서를 생성한다.

---

## 1. 전체 아키텍처

```text
[운영자]
   ↓ 챗봇 프롬프트 입력
[Frontend / CENOps Copilot UI]
   ↓ /api/chat
[Backend / FastAPI Orchestrator]
   ├─ [A-SERVER Agent / WEB-01] 로그·상태·로컬문서 조회
   ├─ [B-SERVER Agent / WAS-01] 로그·상태·로컬문서 조회
   ├─ [C-SERVER Agent / DB-01] 로그·상태·로컬문서 조회
   ├─ [PostgreSQL + pgvector] 중앙 RAG 문서 검색
   ├─ [OpenAI API] 원인 후보 분석 및 답변 생성
   └─ [Report Module] 장애 분석 보고서 생성
   ↓
[Frontend]
   └─ 원인 후보 Top 3 / 근거 로그 / 조회성 Command / 보고서 표시
```

Railway 프로토타입 단계에서는 Private LLM 대신 OpenAI API를 사용합니다. 상용화 단계에서는 Backend의 LLM 호출부를 Private LLM Endpoint로 교체할 수 있도록 분리했습니다.

---

## 2. 디렉터리 구조

```text
cenops-copilot-railway/
├─ frontend/                 # React + Vite UI
├─ backend/                  # FastAPI Orchestrator
├─ mock-agent/               # Railway Mock Agent 서비스. 필요 시 3개 배포
├─ real-agent/               # 실제 A~C 서버 설치용 Agent
├─ db/                       # PostgreSQL + pgvector Schema
├─ docs/                     # Railway 배포 통합 매뉴얼
├─ scripts/                  # 테스트 스크립트
└─ README.md
```

---

## 3. Railway 권장 구성

### 3.1 최소 구성

```text
Railway Project
├─ frontend                  # Root Directory: /frontend
├─ backend                   # Root Directory: /backend
└─ PostgreSQL + pgvector     # Railway DB 서비스
```

이 구성은 Backend 내부 Mock 데이터를 사용합니다. 가장 빠르게 제안서 캡처를 만들 수 있습니다.

### 3.2 제안서 권장 구성

```text
Railway Project
├─ frontend                  # CENOps Copilot UI
├─ backend                   # Orchestrator
├─ PostgreSQL + pgvector     # RAG/장애/보고서 저장소
├─ mock-agent-web-01         # WEB-01 로그 수집 Mock
├─ mock-agent-was-01         # WAS-01 로그 수집 Mock
└─ mock-agent-db-01          # DB-01 로그 수집 Mock
```

### 3.3 실서버 A~C Agent 연계 구성

```text
Railway Project
├─ frontend
├─ backend
└─ PostgreSQL + pgvector

External or Internal Servers
├─ A-SERVER / WEB-01 / real-agent
├─ B-SERVER / WAS-01 / real-agent
└─ C-SERVER / DB-01 / real-agent
```

실서버 Agent는 Railway가 아니라 실제 서버 A~C에 설치하는 구조입니다. 다만 외부 접근 테스트가 어려우면 real-agent를 Railway에 3개 배포해 실서버 연계와 유사하게 검증할 수 있습니다.

---

## 4. 사전 준비

### 4.1 필수 계정 및 도구

- GitHub 계정
- Railway 계정
- OpenAI API Key
- Git
- 선택: Railway CLI
- 선택: Docker

### 4.2 OpenAI API Key 준비

Railway 프로토타입은 외부 LLM을 사용합니다. Backend 서비스 환경변수에 다음 값을 등록합니다.

```text
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

OpenAI API Key가 없으면 Backend는 내장된 deterministic fallback 분석 로직으로 동작합니다. 다만 제안서에는 실제 OpenAI API 연동 캡처가 더 설득력이 있습니다.

---

## 5. GitHub 업로드

로컬에서 압축을 해제한 후 GitHub Repository로 업로드합니다.

```bash
git init
git add .
git commit -m "CENOps Copilot Railway prototype"
git branch -M main
git remote add origin https://github.com/<YOUR_ID>/<YOUR_REPO>.git
git push -u origin main
```

---

## 6. Railway 프로젝트 생성

1. Railway Dashboard 접속
2. `New Project` 선택
3. `Deploy from GitHub repo` 선택
4. 업로드한 Repository 선택
5. 먼저 Backend 서비스를 생성하거나, 전체 Repository에서 서비스별 Root Directory를 지정합니다.

Railway 모노레포 배포에서는 각 서비스의 Root Directory를 지정해야 합니다.

---

## 7. PostgreSQL + pgvector 구성

### 7.1 PostgreSQL 서비스 추가

Railway Project에서 다음을 수행합니다.

1. `New` 또는 `Add Service` 선택
2. `Database` 선택
3. PostgreSQL 또는 pgvector 지원 템플릿 선택
4. 생성 후 Variables 탭에서 `DATABASE_URL` 확인

주의사항:

- Railway 표준 PostgreSQL 이미지에는 pgvector가 없을 수 있습니다.
- RAG 벡터 검색까지 실제로 검증하려면 pgvector 템플릿 사용을 권장합니다.
- 본 소스의 기본 RAG는 파일 기반 lexical search fallback도 지원하므로, pgvector가 없어도 MVP 시연은 가능합니다.

### 7.2 Schema 적용

`db/schema.sql`을 PostgreSQL에 적용합니다.

로컬에서 접속 가능한 경우:

```bash
psql "$DATABASE_URL" -f db/schema.sql
```

Railway Console 또는 별도 DB Client를 사용해도 됩니다.

---

## 8. Backend 배포

### 8.1 서비스 생성

Railway에서 GitHub Repository를 선택한 뒤 Backend 서비스의 Root Directory를 다음으로 지정합니다.

```text
/backend
```

### 8.2 Backend 환경변수

Backend 서비스 Variables 탭에 다음을 등록합니다.

```text
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
DATABASE_URL=${{Postgres.DATABASE_URL}}
FRONTEND_ORIGIN=https://<frontend-service>.up.railway.app
```

Mock Agent를 별도 서비스로 배포하지 않을 경우 아래 값은 비워둡니다.

```text
AGENT_WEB_URL=
AGENT_WAS_URL=
AGENT_DB_URL=
```

실제 A~C 서버 Agent와 연동할 경우 다음을 추가합니다.

```text
SERVER_A_AGENT_URL=https://<a-server-agent-url>
SERVER_B_AGENT_URL=https://<b-server-agent-url>
SERVER_C_AGENT_URL=https://<c-server-agent-url>
SERVER_AGENT_TOKEN=<공통_토큰>
SERVER_QUERY_TIMEOUT=10
```

### 8.3 Backend 배포 확인

배포 후 Public Domain을 생성하고 다음 URL로 확인합니다.

```text
https://<backend-service>.up.railway.app/health
```

정상 응답 예시:

```json
{
  "status": "ok",
  "service": "cenops-copilot-backend"
}
```

---

## 9. Frontend 배포

### 9.1 서비스 생성

Railway에서 동일 Repository로 새 서비스를 추가하고 Root Directory를 다음으로 지정합니다.

```text
/frontend
```

### 9.2 Frontend 환경변수

Frontend 서비스 Variables 탭에 Backend URL을 지정합니다.

```text
VITE_API_BASE_URL=https://<backend-service>.up.railway.app
```

변경 후 반드시 재배포합니다. Vite 계열 Frontend 환경변수는 빌드 시점에 반영됩니다.

### 9.3 Frontend 확인

```text
https://<frontend-service>.up.railway.app
```

화면에서 다음 항목이 보이면 정상입니다.

- CENOps Copilot 챗봇 인터페이스
- 대상 서버 선택: 자동선택 / A-SERVER / B-SERVER / C-SERVER
- 예시 질문
- 운영문서 RAG 검색
- Mock Agent 상태 수집
- 조회성 자연어 Command
- 장애 보고서 생성

---

## 10. Mock Agent 3대 배포

Mock Agent는 실제 서버가 없어도 WEB/WAS/DB 3대 Agent 연동 구조를 보여주기 위한 컴포넌트입니다.

### 10.1 WEB-01 Mock Agent

새 Railway 서비스 생성:

```text
Root Directory: /mock-agent
Service Name: mock-agent-web-01
```

환경변수:

```text
AGENT_NAME=WEB-01
AGENT_ROLE=WEB
```

배포 후 URL 예시:

```text
https://mock-agent-web-01.up.railway.app
```

Backend 환경변수에 등록:

```text
AGENT_WEB_URL=https://mock-agent-web-01.up.railway.app
```

### 10.2 WAS-01 Mock Agent

```text
Root Directory: /mock-agent
Service Name: mock-agent-was-01
AGENT_NAME=WAS-01
AGENT_ROLE=WAS
```

Backend 환경변수:

```text
AGENT_WAS_URL=https://mock-agent-was-01.up.railway.app
```

### 10.3 DB-01 Mock Agent

```text
Root Directory: /mock-agent
Service Name: mock-agent-db-01
AGENT_NAME=DB-01
AGENT_ROLE=DB
```

Backend 환경변수:

```text
AGENT_DB_URL=https://mock-agent-db-01.up.railway.app
```

---

## 11. 실제 A~C 서버 Agent 설치

실제 서버 A~C에서 챗봇 프롬프트 질의를 받으려면 `real-agent`를 각 서버에 설치합니다.

### 11.1 서버 매핑

```text
A-SERVER = WEB-01 = Nginx / Web 계층
B-SERVER = WAS-01 = Tomcat / WAS 계층
C-SERVER = DB-01 = PostgreSQL / DB 계층
```

### 11.2 Docker 방식 설치 예시

각 서버에서 `real-agent` 디렉터리를 배포한 뒤 실행합니다.

A-SERVER / WEB-01:

```bash
cd real-agent
docker build -t cenops-real-agent:0.1 .
docker run -d --name cenops-agent-a \
  -p 8080:8080 \
  -e AGENT_NAME=A-SERVER \
  -e AGENT_ROLE=WEB \
  -e AGENT_TOKEN='<공통_토큰>' \
  -e LOG_PATHS='/var/log/nginx/error.log,/var/log/messages,/var/log/syslog' \
  -v /var/log:/var/log:ro \
  -v /opt/cenops-agent/docs:/app/docs:ro \
  cenops-real-agent:0.1
```

B-SERVER / WAS-01:

```bash
docker run -d --name cenops-agent-b \
  -p 8080:8080 \
  -e AGENT_NAME=B-SERVER \
  -e AGENT_ROLE=WAS \
  -e AGENT_TOKEN='<공통_토큰>' \
  -e LOG_PATHS='/app/tomcat/logs/catalina.out,/var/log/messages,/var/log/syslog' \
  -v /app/tomcat/logs:/app/tomcat/logs:ro \
  -v /var/log:/var/log:ro \
  -v /opt/cenops-agent/docs:/app/docs:ro \
  cenops-real-agent:0.1
```

C-SERVER / DB-01:

```bash
docker run -d --name cenops-agent-c \
  -p 8080:8080 \
  -e AGENT_NAME=C-SERVER \
  -e AGENT_ROLE=DB \
  -e AGENT_TOKEN='<공통_토큰>' \
  -e LOG_PATHS='/var/log/postgresql/postgresql.log,/var/log/messages,/var/log/syslog' \
  -v /var/log:/var/log:ro \
  -v /opt/cenops-agent/docs:/app/docs:ro \
  cenops-real-agent:0.1
```

### 11.3 Python 직접 실행 방식

Docker를 사용할 수 없는 경우:

```bash
cd real-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export AGENT_NAME=A-SERVER
export AGENT_ROLE=WEB
export AGENT_TOKEN='<공통_토큰>'
export LOG_PATHS='/var/log/nginx/error.log,/var/log/messages,/var/log/syslog'
export DOCS_DIR='/opt/cenops-agent/docs'
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### 11.4 보안 권장사항

- Agent는 조회성 작업만 수행합니다.
- 로그와 문서는 read-only volume으로 마운트합니다.
- `AGENT_TOKEN`을 설정하고 Backend에도 동일한 `SERVER_AGENT_TOKEN`을 등록합니다.
- 운영망에서는 Agent URL을 인터넷에 직접 노출하지 않고 VPN, 방화벽, Reverse Proxy, 사설망을 통해 접근하도록 설계합니다.
- 본 프로토타입 Agent는 파일 수정·삭제·서비스 재시작 명령을 수행하지 않습니다.

---

## 12. 실제 A~C 서버 Agent URL 등록

A~C 서버가 Backend에서 접근 가능한 URL을 확보한 뒤 Backend 환경변수에 등록합니다.

```text
SERVER_A_AGENT_URL=http://<A-SERVER-IP>:8080
SERVER_B_AGENT_URL=http://<B-SERVER-IP>:8080
SERVER_C_AGENT_URL=http://<C-SERVER-IP>:8080
SERVER_AGENT_TOKEN=<공통_토큰>
```

Railway Backend에서 사내 서버로 접근이 어려운 경우 다음 중 하나가 필요합니다.

1. 테스트용 Agent를 Railway에 배포한다.
2. A~C 서버를 공인 테스트 URL로 임시 노출한다.
3. ngrok, Cloudflare Tunnel, VPN 등 터널링을 사용한다.
4. 실제 폐쇄망 상용 구조에서는 Railway가 아니라 내부망 Appliance로 Backend를 이전한다.

---

## 13. A~C 서버 질의 테스트

### 13.1 서버 목록 확인

```bash
curl https://<backend-service>.up.railway.app/api/servers
```

응답 예시:

```json
{
  "servers": [
    {"key": "A", "label": "A-SERVER / WEB-01", "role": "WEB", "mode": "real-agent"},
    {"key": "B", "label": "B-SERVER / WAS-01", "role": "WAS", "mode": "real-agent"},
    {"key": "C", "label": "C-SERVER / DB-01", "role": "DB", "mode": "real-agent"}
  ]
}
```

### 13.2 챗봇 프롬프트 기반 A서버 질의

```bash
curl -X POST https://<backend-service>.up.railway.app/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"A서버 최근 Nginx 502 오류 로그 확인해줘","target":"A"}'
```

기대 결과:

- A-SERVER / WEB-01 Agent 호출
- Nginx error.log 필터링
- 조회성 Command 제안
- 관련 RAG 문서 표시
- 보고서 Markdown 생성

### 13.3 챗봇 프롬프트 기반 B서버 질의

```bash
curl -X POST https://<backend-service>.up.railway.app/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"B서버 Tomcat HikariPool timeout 로그와 조치 문서 알려줘","target":"B"}'
```

### 13.4 챗봇 프롬프트 기반 C서버 질의

```bash
curl -X POST https://<backend-service>.up.railway.app/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"C서버 DB 연결 상태와 5432 세션 상태 확인해줘","target":"C"}'
```

---

## 14. A~C 서버 로컬 RAG 문서 질의 테스트

실제 A~C 서버에 `/opt/cenops-agent/docs` 디렉터리를 만들고 Markdown 또는 TXT 문서를 넣습니다.

예시:

```bash
sudo mkdir -p /opt/cenops-agent/docs
sudo tee /opt/cenops-agent/docs/tomcat_502_runbook.md > /dev/null <<'EOF'
# Tomcat 502 장애 조치 문서

## HikariPool timeout
WAS에서 HikariPool timeout이 발생하면 DB connection pool max size, DB max connection, slow query, lock wait를 순차 확인한다.

## 조회 명령
- tail -n 150 /app/tomcat/logs/catalina.out
- ps -ef | grep -E 'tomcat|java' | grep -v grep
EOF
```

Backend에서 RAG 질의:

```bash
curl -X POST https://<backend-service>.up.railway.app/api/server-rag/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"B서버 Tomcat 502 HikariPool timeout 조치 절차 알려줘","target":"B","top_k":5,"include_agent_local_docs":true}'
```

챗봇 UI에서도 다음과 같이 입력합니다.

```text
B서버 Tomcat 502 HikariPool timeout 조치 문서 찾아줘
```

기대 결과:

- 중앙 RAG 문서 검색
- B-SERVER Agent의 `/rag/search` 호출
- B-SERVER 로컬 운영문서 검색 결과 병합
- 챗봇 결과 화면에 참조 문서와 근거 표시

---

## 15. Web/WAS 502 장애 시나리오 테스트

Frontend 챗봇 입력창에 다음을 입력합니다.

```text
Zenius 알림: WEB-01 502 오류 발생. 원인 분석해줘.
```

Backend 처리 흐름:

```text
1. /api/chat 수신
2. Web/WAS 502 장애 유형으로 분류
3. A-SERVER / WEB-01 로그 수집
4. B-SERVER / WAS-01 로그 수집
5. C-SERVER / DB-01 로그 수집
6. 중앙 RAG + Agent 로컬 RAG 검색
7. OpenAI API 분석
8. 원인 후보 Top 3 산출
9. 조회성 Command 제안
10. 장애 분석 보고서 생성
```

예상 결과:

```text
1순위: WAS Connection Pool 고갈
2순위: DB 응답 지연 또는 세션 과다
3순위: Nginx upstream timeout
```

---

## 16. 제안서 캡처 권장 화면

제안서에는 다음 4개 화면을 캡처하는 것을 권장합니다.

1. CENOps Copilot 챗봇 입력 화면
2. Web/WAS 502 원인 후보 Top 3 결과 화면
3. Agent 3대 수집 결과 화면
4. 장애 분석 보고서 미리보기 화면

캡처 화면 설명 문구 예시:

```text
Railway 기반 프로토타입에서 운영자가 Zenius 알림 문구를 입력하면, CENOps Copilot이 A~C 서버 Agent 로그와 RAG 운영문서를 결합하여 Web/WAS 502 장애 원인 후보 Top 3와 근거 로그, 조회성 Command, 장애 보고서를 제시하는 End-to-End 흐름을 검증하였다.
```

---

## 17. 장애 대응 및 트러블슈팅

### 17.1 Frontend에서 Backend 호출 실패

확인 항목:

```text
VITE_API_BASE_URL=https://<backend-service>.up.railway.app
FRONTEND_ORIGIN=https://<frontend-service>.up.railway.app
```

Vite 환경변수 변경 후에는 Frontend 재배포가 필요합니다.

### 17.2 Backend에서 OpenAI API 실패

확인 항목:

```text
OPENAI_API_KEY 값 존재 여부
OPENAI_MODEL 값 확인
Railway Variables 재배포 여부
```

API Key가 없으면 fallback 분석으로 동작합니다.

### 17.3 A~C 서버 Agent 연결 실패

확인 항목:

```text
SERVER_A_AGENT_URL / SERVER_B_AGENT_URL / SERVER_C_AGENT_URL
SERVER_AGENT_TOKEN
Agent /health 응답
방화벽 및 포트 8080 허용 여부
```

Agent 연결 실패 시 Backend는 Mock 데이터로 fallback합니다. 응답의 `collection_mode`가 다음 중 하나로 표시됩니다.

```text
real-agent                  # 실제 Agent 수집 성공
real-agent-fallback-mock     # 실제 Agent 실패 후 Mock fallback
mock-no-real-agent-url       # Agent URL 미설정으로 Mock 사용
```

### 17.4 RAG 결과가 적게 나오는 경우

확인 항목:

- `backend/data/docs`에 Markdown 문서가 존재하는지 확인
- 실제 Agent 서버의 `DOCS_DIR` 경로에 문서가 있는지 확인
- 질문에 `Tomcat`, `502`, `HikariPool`, `Nginx`, `DB`, `Connection` 등 검색 키워드를 포함

---

## 18. 운영상 제한사항

본 프로토타입은 공모전 제출 및 시연용 MVP입니다.

구현된 범위:

- Railway 기반 UI/Backend 배포
- Mock Agent 또는 실제 A~C Agent 질의
- 중앙 RAG 문서 검색
- Agent 로컬 문서 검색
- 조회성 Command 제안
- OpenAI API 기반 분석
- 장애 보고서 Markdown 생성

구현하지 않은 범위:

- 폐쇄망 Private LLM 실제 배포
- 실서버 변경 명령 자동 실행
- Zenius 공식 API 실시간 연동
- 운영망 보안 심사 대응 수준의 Agent 인증·감사·암호화 체계

제안서 표현 시 다음과 같이 표기하는 것을 권장합니다.

```text
Railway 기반 프로토타입에서 핵심 동작을 검증하였으며, 상용화 단계에서는 폐쇄망 Private LLM, 실서버 Agent, Zenius API/Webhook/Syslog 연동 구조로 확장 가능하다.
```
