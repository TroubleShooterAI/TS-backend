---
name: Bug Report
about: 문제 발생 시 원인 및 상황을 기록하는 템플릿입니다.
title: '[BUG] '
labels: 'bug'
assignees: ''
---

## 📌 버그 개요
어떤 버그인지 간략하게 설명해 주세요.

## 📱 발생 환경
- OS: [e.g. macOS, Ubuntu]
- Python Version: [e.g. 3.11]
- Docker/Redis 여부: [e.g. Docker 실행 중]

## 🔄 재현 방법
버그를 재현할 수 있는 순서를 작성해 주세요.
1. `uvicorn main:app --reload` 실행
2. POST `/api/v1/logs`에 잘못된 포맷 전달
3. ...

## 💥 예상 동작 vs 실제 동작
- **예상 동작**: 422 Unprocessable Entity 에러 반환
- **실제 동작**: 500 Internal Server Error 발생

## 📜 로그 / StackTrace
```text
(발생한 에러 로그나 StackTrace를 여기에 붙여넣어 주세요)