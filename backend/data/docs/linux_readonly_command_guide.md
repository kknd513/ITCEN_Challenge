# 리눅스 조회성 자연어 Command 가이드

## 목적

CENOps Copilot은 운영자가 자연어로 요청한 내용을 조회성 명령어로 변환한다. 파일 삭제, 권한 변경, 서비스 재시작, 프로세스 종료 등 변경성 명령어는 차단한다.

## 허용 명령어 예시

| 자연어 | 조회성 Command |
|---|---|
| WEB 서버 최근 오류 로그 보여줘 | tail -n 100 /var/log/nginx/error.log |
| WAS Tomcat 오류 확인해줘 | tail -n 150 /app/tomcat/logs/catalina.out |
| WAS 프로세스 상태 확인해줘 | ps -ef \| grep -E 'tomcat\|java' \| grep -v grep |
| DB 연결 상태 확인해줘 | ss -tnp \| grep ':5432' \| head -n 50 |
| 디스크 사용률 확인해줘 | df -h |
| 메모리 사용률 확인해줘 | free -m |

## 차단 명령어

다음 명령어는 프로토타입 및 상용 환경 모두에서 기본 차단한다.

```text
rm, mv, cp, chmod, chown, kill, shutdown, reboot, systemctl restart, service restart, vi, vim, nano, dd, mkfs, fdisk, sudo
```

## 운영 원칙

- CENOps Copilot은 명령어를 제안하거나 조회 결과를 요약한다.
- 변경성 조치 또는 서비스 재시작은 운영자 승인 절차를 거쳐야 한다.
- 장애 원인은 확정 표현 대신 가능성 높은 후보로 제시한다.
