from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import redis
import datetime
from dotenv import load_dotenv
import os
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr

# 환경변수 로드
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key_for_dev")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# DB 설정(SQLite)   
SQLALCHEMY_DATABASE_URL = "sqlite:///./troubleshooter.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Pydantic Schemas
class SignupRequest(BaseModel):
    email: EmailStr
    password: str


# DB 테이블 정의
class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    logs = relationship("ErrorLogDB", back_populates="owner")

class ErrorLogDB(Base):
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id")) # 외래키 추가
    service_name = Column(String, index=True)
    exception_type = Column(String)
    message = Column(Text)
    stack_trace = Column(Text)
    ai_analysis = Column(Text)
    status = Column(String, default="UNSOLVED") #UNSOLVED, IN_PROGRESS, RESOLVED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("UserDB", back_populates="logs") # 역방향 관계 추가

Base.metadata.create_all(bind=engine)

# FastAPI 앱 및 CORS 설정
app = FastAPI(title="TroubleShooter AI - Main Backend")

# React(Vite) 개발 서버 포트 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        ],   # 허용할 프론트엔드 출처
    allow_credentials=True,  # 쿠키 및 인증 헤더 허용
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 -> GET, POST, ...
    allow_headers=["*"],   # 모든 요청 헤더 허용
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 인증 헬퍼 함수
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="인증 자격 증명이 유효하지 않습니다.")
    except JWTError:
        raise HTTPException(status_code=401, detail="인증 자격 증명이 유효하지 않습니다.")
    
    user = db.query(UserDB).filter(UserDB.email == email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    return user

# API 앤드포인트
@app.post("/api/v1/auth/signup")
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    # 1. 기존 유저 존재 확인
    db_user = db.query(UserDB).filter(UserDB.email == req.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
    
    # 2. 비밀번호 해싱 및 유저 생성
    hashed_pwd = get_password_hash(req.password)
    new_user = UserDB(email=req.email, hashed_password=hashed_pwd)
    
    db.add(new_user)
    db.commit()
    return {"message": "회원가입이 완료되었습니다."}

@app.post("/api/v1/auth/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
    ):
    user = db.query(UserDB).filter(UserDB.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="이메일 또는 비밀번호가 잘못되었습니다.")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type":"bearer"}


# 에러 목록 조회 API
@app.get("/api/v1/errors")
def get_user_errors(
    current_user: UserDB = Depends(get_current_user), 
    db: Session = Depends(get_db)
    ):
    return db.query(ErrorLogDB).filter(ErrorLogDB.user_id == current_user.id).order_by(ErrorLogDB.created_at.desc()).all()

# 특정 에러 상세 & Gemini 분석 결과 조회 API
@app.get("/api/v1/errors/{error_id}")
def get_error_detail(
    error_id: int, 
    current_user : UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
    ):
    error_log = db.query(ErrorLogDB).filter(ErrorLogDB.id == error_id, ErrorLogDB.user_id == current_user.id).first()
    if not error_log:
        raise HTTPException(status_code=404, detail="해당 에러 로그를 찾을 수 없습니다.")
    return error_log