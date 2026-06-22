# 최근 정보화사업 산출물 임의생성 문서

## 시스템 구성 개요

본 정보화사업 시스템은 WEB, WAS, DB 3계층 구조로 구성된다.

| 구분 | 호스트명 | 역할 | 주요 로그 |
|---|---|---|---|
| WEB | WEB-01 | Nginx Reverse Proxy | /var/log/nginx/error.log |
| WAS | WAS-01 | Tomcat Application Server | /app/tomcat/logs/catalina.out |
| DB | DB-01 | PostgreSQL | /var/log/postgresql/postgresql.log |

## 서비스 흐름

사용자 요청은 WEB-01 Nginx를 거쳐 WAS-01 Tomcat으로 전달된다. WAS-01은 DB-01 PostgreSQL에 연결하여 주문/조회 데이터를 처리한다. WAS 응답이 지연되면 WEB-01에서는 upstream timeout 또는 502 Bad Gateway가 발생할 수 있다.

## 주요 포트

| 구간 | 포트 | 설명 |
|---|---:|---|
| Client → WEB | 443 | HTTPS |
| WEB → WAS | 8080 | Tomcat upstream |
| WAS → DB | 5432 | PostgreSQL |

## 장애 영향도

WEB/WAS 502 장애 발생 시 사용자 주문 조회, 신청 처리, 관리자 조회 화면이 영향을 받을 수 있다. 단, 정적 파일 서비스는 정상일 수 있다.

## 운영자 확인 순서

1. Zenius 알림 발생 시각 확인
2. WEB-01 Nginx error.log 조회
3. WAS-01 catalina.out 오류 로그 조회
4. DB-01 세션 및 연결 지연 로그 조회
5. 동일 시각대 배포, 배치, 트래픽 증가 여부 확인
6. 원인 후보별 근거 로그 정리 후 장애 보고서 작성
