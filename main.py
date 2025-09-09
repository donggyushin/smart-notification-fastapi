from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, engine, Base
from models import DeviceCreate, DeviceResponse
from device_service import register_device, get_active_devices
import logging

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Notification API", version="0.1.0")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # DB 연결 테스트
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "message": "Smart Notification API is running", "database": "connected"}
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return {"status": "unhealthy", "message": "Database connection failed", "error": str(e)}

@app.post("/devices", response_model=DeviceResponse)
async def register_device_endpoint(device: DeviceCreate, db: Session = Depends(get_db)):
    """디바이스 등록 및 FCM 토큰 업데이트"""
    try:
        return register_device(db, device)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Device registration failed: {str(e)}")

@app.get("/devices", response_model=list[DeviceResponse])
async def get_devices_endpoint(db: Session = Depends(get_db)):
    """활성 디바이스 목록 조회"""
    return get_active_devices(db)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
