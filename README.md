# 🛠️ TroubleShooter AI - Backend

> **개발 프로젝트 장애 대응 및 트러블슈팅 자동화 AI 에이전트**  
> 백엔드 애플리케이션에서 발생하는 에러 로그(StackTrace)를 실시간으로 수집하고, AI(LLM)와 코드베이스 RAG를 통해 원인 분석 및 해결 가이드를 제공하는 플랫폼입니다.

---

## 📌 Key Features

* **Real-time Log Ingestion**: 타겟 애플리케이션에서 발생하는 에러 로그 및 StackTrace 비동기 수신
* **Asynchronous Message Queue**: Redis Queue를 활용한 백그라운드 로그 처리 (타겟 서비스 지연 방지)
* **Codebase RAG & Root Cause Analysis**: 에러 발생 위치의 소스 코드를 Vector DB에서 탐색하여 LLM 분석
* **TroubleShooting Wiki Generation**: 분석된 에러 원인 및 핫픽스 가이드를 Markdown 형태의 카드로 자동 문서화

---

## 🏗️ Architecture
(첨부 예정)


## 🛠️ Tech Stack
* **Framework**: Python 3.9+, FastAPI, Pydantic
* **Message Broker/ Cache**: Redis
* **Server**: Uvicorn
* **Version Control**: Git/ Github

## 📂 Project Structure
(작성 예정)