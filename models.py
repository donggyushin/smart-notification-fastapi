from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from database import Base
import uuid

class Device(Base):
    __tablename__ = "devices"
    
    device_uuid = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    fcm_token = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Device(device_uuid='{self.device_uuid}', is_active={self.is_active})>"