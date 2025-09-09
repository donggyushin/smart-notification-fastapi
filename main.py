from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, engine, Base
from models import Device, DeviceCreate, DeviceResponse
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
async def register_device(device: DeviceCreate, db: Session = Depends(get_db)):
    """디바이스 등록 및 FCM 토큰 업데이트"""
    try:
        # 기존 device_uuid가 있는지 확인
        existing_device = db.query(Device).filter(Device.device_uuid == device.device_uuid).first()
        
        if existing_device:
            # 기존 디바이스의 FCM 토큰 업데이트
            existing_device.fcm_token = device.fcm_token
            existing_device.is_active = True
            db.commit()
            db.refresh(existing_device)
            return existing_device
        
        # 새 디바이스 생성
        new_device = Device(
            device_uuid=device.device_uuid,
            fcm_token=device.fcm_token
        )
        db.add(new_device)
        db.commit()
        db.refresh(new_device)
        return new_device
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Device registration failed: {str(e)}")

@app.get("/devices", response_model=list[DeviceResponse])
async def get_devices(db: Session = Depends(get_db)):
    """활성 디바이스 목록 조회"""
    devices = db.query(Device).filter(Device.is_active == True).all()
    return devices

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
