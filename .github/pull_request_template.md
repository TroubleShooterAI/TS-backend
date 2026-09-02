## 📌 PR 개요
이 PR에서 작업한 내용의 요약을 작성해 주세요.

## 🛠️ 주요 변경 사항
- [x] FastAPI 로그 수신 API 구현 (`/api/v1/logs`)
- [x] Pydantic 기반 LogPayload 스키마 정의 (`schemas.py`)
- [x] Redis log_queue를 감시하는 비동기 Worker 기초 작업 (`worker.py`)

## 🔗 관련 이슈
- Fixes # (이슈 번호가 있다면 작성해 주세요)
- Ref #

## 🧪 테스트 결과
테스트 방법 및 결과를 스크린샷이나 실행 로그로 공유해 주세요.
- [x] cURL을 통한 POST 테스트 완료 (HTTP 202 응답)
- [x] Redis worker 수신 로그 출력 확인

## 📸 스크린샷 / 실행 로그 (선택)