from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db, engine, Base
from models import DeviceCreate, DeviceResponse, NewsFeedResponse
from device_service import register_device, get_active_devices, get_device_tokens
from news_service import get_news_feed_with_cursor
from scheduler_service import news_scheduler
from firebase_service import firebase_service
from typing import Optional
import logging
import atexit

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Notification API", version="0.1.0")

# Startup event to initialize scheduler
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logging.info("Starting Smart Notification API...")
    # Start the news scheduler
    news_scheduler.start_scheduler()

# Shutdown event to cleanup scheduler
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on shutdown"""
    logging.info("Shutting down Smart Notification API...")
    news_scheduler.stop_scheduler()

# Also register cleanup on process exit
atexit.register(news_scheduler.stop_scheduler)

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

@app.get("/news/feed", response_model=NewsFeedResponse)
async def get_news_feed_endpoint(
    db: Session = Depends(get_db),
    cursor_id: Optional[int] = Query(None, description="Cursor ID for pagination (last item ID from previous request)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return (1-100)"),
    min_score: Optional[int] = Query(None, ge=-10, le=10, description="Minimum score filter (-10 to 10)"),
    max_score: Optional[int] = Query(None, ge=-10, le=10, description="Maximum score filter (-10 to 10)")
):
    """뉴스 피드 조회 (무한 스크롤 지원)"""
    try:
        # Validate score range
        if min_score is not None and max_score is not None and min_score > max_score:
            raise HTTPException(status_code=400, detail="min_score cannot be greater than max_score")
        
        result = get_news_feed_with_cursor(
            db=db,
            cursor_id=cursor_id,
            limit=limit,
            min_score=min_score,
            max_score=max_score
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch news feed: {str(e)}")

@app.get("/admin/scheduler/status")
async def get_scheduler_status():
    """스케줄러 상태 조회 (관리자용)"""
    return news_scheduler.get_scheduler_status()

@app.post("/admin/scheduler/run-now")
async def trigger_news_analysis():
    """뉴스 분석 수동 실행 (관리자용)"""
    try:
        # Run the task in background to avoid timeout
        import asyncio
        asyncio.create_task(news_scheduler.daily_news_analysis_task())
        return {"message": "News analysis task started in background"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger news analysis: {str(e)}")

@app.post("/admin/test/push-notification")
async def test_push_notification(
    title: str = "📱 Test Notification",
    body: str = "This is a test push notification to all registered devices!",
    db: Session = Depends(get_db)
):
    """테스트용 푸시 알림 전송 - 모든 활성 디바이스에 알림 발송 (관리자용)"""
    try:
        # Get all active device tokens
        tokens = get_device_tokens(db, active_only=True)
        
        if not tokens:
            return {
                "message": "No active devices found",
                "success_count": 0,
                "failure_count": 0,
                "total_devices": 0
            }
        
        # Additional data payload for test notification
        data = {
            "type": "test_notification",
            "test_id": f"test_{int(__import__('time').time())}",
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }
        
        # Send multicast notification to all devices
        result = await firebase_service.send_multicast_notification(
            tokens=tokens,
            title=title,
            body=body,
            data=data
        )
        
        return {
            "message": f"Test notification sent to {len(tokens)} devices",
            "success_count": result["success_count"],
            "failure_count": result["failure_count"],
            "total_devices": len(tokens),
            "failed_tokens_count": len(result["failed_tokens"]),
            "notification_details": {
                "title": title,
                "body": body,
                "data": data
            }
        }
        
    except Exception as e:
        logging.error(f"Failed to send test notification: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to send test notification: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
