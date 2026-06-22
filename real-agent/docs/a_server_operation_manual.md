# A-SERVER / WEB-01 운영문서

## Web/WAS 502 발생 시 1차 확인
- Nginx `error.log`에서 `upstream timed out`, `502 Bad Gateway`, `connect() failed` 패턴을 확인한다.
- WAS-01 Tomcat 응답 지연 또는 DB Connection Pool 고갈 여부와 함께 확인한다.
- 조회성 명령어 예시: `tail -n 100 /var/log/nginx/error.log`.

## 주의사항
- 운영자 승인 없이 `systemctl restart nginx`, `rm`, `truncate` 등 변경 명령은 수행하지 않는다.
