from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import redis
import datetime

# DB 설정(SQLite)   
SQLALCHEMY_DATABASE_URL = "sqlite:///./troubleshooter.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# DB 테이블 정의
class ErrorLogDB(Base):
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, index=True)
    exception_type = Column(String)
    message = Column(Text)
    stack_trace = Column(Text)
    ai_analysis = Column(Text)
    status = Column(String, default="UNSOLVED") #UNSOLVED, IN_PROGRESS, RESOLVED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bing=engine)

# FastAPI 앱 및 CORS 설정
app = FastAPI(title="TroubleShooter AI - Main Backend")

# React(Vite) 개발 서버 포트 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API 앤드포인트

@app.get("/health")
def health_check():
    return {"status": "ok"}

# 에러 목록 조회 API
@app.get("/api/v1/errors")
def get_errors(db: Session = Depends(get_db)):
    return db.query(ErrorLogDB).order_by(ErrorLogDB.created_at.desc()).all()

# 특정 에러 상세 & Gemini 분석 결과 조회 API
@app.get("/api/v1/errors/{error_id}")
def get_error_detail(error_id: int, db: Session = Depends(get_db)):
    error_log = db.query(ErrorLogDB).filter(ErrorLogDB.id == error_id).first()
    if not error_log:
        raise HTTPException(status_code=404, detail="Error log not found")
    return error_log