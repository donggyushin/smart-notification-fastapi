from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, Date, JSON
from sqlalchemy.sql import func
from database import Base
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

class Device(Base):
    __tablename__ = "devices"
    
    device_uuid = Column(String, primary_key=True, unique=True, index=True)
    fcm_token = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Device(device_uuid='{self.device_uuid}', is_active={self.is_active})>"

# SQLAlchemy model for database storage
class NewsAnalysis(Base):
    __tablename__ = "news_analysis"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    summarize = Column(Text, nullable=False)
    url = Column(Text, unique=True, nullable=False, index=True)  # Unique constraint for duplicate prevention
    published_date = Column(DateTime(timezone=True), nullable=False)
    score = Column(Integer, nullable=False)
    tickers = Column(JSON, nullable=False)  # Store list of tickers as JSON
    save = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<NewsAnalysis(url='{self.url}', score={self.score}, tickers={self.tickers})>"

# Pydantic models for Device API
class DeviceCreate(BaseModel):
    device_uuid: str
    fcm_token: str

class DeviceResponse(BaseModel):
    device_uuid: str
    fcm_token: str
    is_active: bool
    
    class Config:
        from_attributes = True

# Pydantic models for News API responses
class NewsResponse(BaseModel):
    id: int
    title: str
    summarize: str
    url: str
    published_date: datetime
    score: int
    tickers: List[str]
    save: bool
    created_at: str
    
    class Config:
        from_attributes = True

class NewsFeedResponse(BaseModel):
    items: List[NewsResponse]
    next_cursor_id: Optional[int] = None
    has_more: bool
    limit: int

# Pydantic model for API responses and CrewAI output
class NewsEntity(BaseModel):
    title: str
    summarize: str
    url: str
    published_date: datetime
    score: int
    tickers: List[str]
    save: bool = False