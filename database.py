import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# Railway에서 DATABASE_URL 환경변수로 제공됨
DATABASE_URL = os.getenv("DATABASE_URL")

# 로컬 개발용 기본값 (필요시 변경)
if not DATABASE_URL:
    DATABASE_URL = "postgresql://user:password@localhost:5432/smart_notification"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Function to get database URL for Alembic
def get_database_url():
    return DATABASE_URL

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()