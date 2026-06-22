# C-SERVER / DB-01 운영문서

## DB 연결 지연 확인
- PostgreSQL 로그에서 connection timeout, lock wait, long running query를 확인한다.
- WAS-01에서 DB 연결 실패가 발생하면 세션 수, lock wait, slow query를 함께 검토한다.
- 조회성 명령어 예시: `ss -tnp | grep ':5432' | head -n 50`.
