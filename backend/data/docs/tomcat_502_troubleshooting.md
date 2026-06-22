# Tomcat Web/WAS 502 장애 조치 운영문서

## 502 Bad Gateway 개요

502 Bad Gateway는 WEB 계층의 Nginx 또는 L4/L7 Proxy가 WAS 응답을 정상적으로 받지 못할 때 발생한다. Web/WAS 구조에서는 Nginx upstream timeout, Tomcat thread pool 고갈, DB connection pool 고갈, DB 응답 지연이 주요 원인이다.

## Nginx upstream timed out

대표 로그:

```text
upstream timed out while reading response header from upstream
GET /api/order/list HTTP/1.1 -> 502 Bad Gateway
```

1차 확인:

```bash
tail -n 100 /var/log/nginx/error.log | grep -Ei 'upstream|502|timeout|error'
```

권장 확인 항목:

- proxy_read_timeout 설정
- upstream WAS 서버 상태
- 같은 시간대 WAS catalina.out 오류 여부
- 사용자 요청 증가 여부

## Tomcat HikariPool Connection Timeout

대표 로그:

```text
HikariPool-1 - Connection is not available, request timed out after 30000ms
java.sql.SQLTransientConnectionException
```

원인 후보:

- DB 응답 지연으로 WAS connection pool 반환 지연
- maxPoolSize 부족
- Long running query 증가
- DB 세션 한도 부족

조회성 확인 명령어:

```bash
tail -n 150 /app/tomcat/logs/catalina.out | grep -Ei 'HikariPool|SocketTimeout|SEVERE|Exception'
ps -ef | grep -E 'tomcat|java' | grep -v grep
```

조치 가이드:

- HikariCP maximumPoolSize, connectionTimeout 설정 확인
- DB active session, lock wait, slow query 확인
- 최근 배포 및 배치 작업 여부 확인
- 즉시 재시작보다 근거 로그 확보 후 영향도 판단

## Tomcat Thread Pool 고갈

대표 지표:

```text
active_threads=200
max_threads=200
```

원인 후보:

- 특정 API 응답 지연
- DB 대기 증가
- 외부 API timeout
- 배치 작업과 온라인 요청 경합

권장 확인:

```bash
jstack <PID> | head
```

운영 정책상 jstack은 시스템 부하를 고려해야 하므로 프로토타입에서는 명령 제안만 수행하고 실제 실행은 운영자 승인 후 진행한다.
