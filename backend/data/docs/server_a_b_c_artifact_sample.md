# A~C 서버 정보화사업 산출물 임의 생성 문서

## 시스템 구성
- A-SERVER / WEB-01: Nginx Reverse Proxy, 사용자 요청 최초 수신, WAS-01 upstream 연계.
- B-SERVER / WAS-01: Tomcat Application Server, 주문/조회 API 처리, DB-01 PostgreSQL 연결.
- C-SERVER / DB-01: PostgreSQL Database, 주문/회원/로그성 데이터 저장.

## Web/WAS 502 장애 연관관계
1. 사용자가 WEB-01로 접속한다.
2. WEB-01 Nginx가 WAS-01 Tomcat으로 요청을 전달한다.
3. WAS-01이 DB-01의 연결을 획득하지 못하거나 응답이 지연되면 Nginx에서 upstream timeout이 발생할 수 있다.
4. 운영자는 WEB-01, WAS-01, DB-01 로그를 같은 시간대 기준으로 교차 확인한다.

## 운영 담당자 확인 순서
- 1순위: B-SERVER/WAS-01 Tomcat `HikariPool` 및 `SocketTimeoutException` 로그 확인.
- 2순위: C-SERVER/DB-01 세션 수, Lock Wait, Slow Query 증가 확인.
- 3순위: A-SERVER/WEB-01 Nginx `upstream timed out` 및 proxy timeout 설정 확인.

## 안전한 조회성 명령어
- A-SERVER: `tail -n 100 /var/log/nginx/error.log | grep -Ei 'upstream|502|timeout|error'`
- B-SERVER: `tail -n 150 /app/tomcat/logs/catalina.out | grep -Ei 'HikariPool|SocketTimeout|SEVERE|Exception'`
- C-SERVER: `ss -tnp | grep ':5432' | head -n 50`
