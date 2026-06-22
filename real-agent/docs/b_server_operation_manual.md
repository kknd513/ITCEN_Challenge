# B-SERVER / WAS-01 운영문서

## Tomcat 502 연계 장애 확인
- `catalina.out`에서 `HikariPool`, `SocketTimeoutException`, `SEVERE`, `Connection is not available` 패턴을 확인한다.
- Thread Pool `active=max` 상태와 DB 세션 증가가 동시에 발생하면 WAS 처리 지연 가능성이 높다.
- 조회성 명령어 예시: `ps -ef | grep -E 'tomcat|java' | grep -v grep`.

## 조치 가이드
- Connection Pool max size, DB max connection, 최근 배포/트래픽 증가를 순차적으로 확인한다.
