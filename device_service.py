from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import Device, DeviceCreate
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

def register_device(db: Session, device: DeviceCreate) -> Device:
    """
    Register a new device or update existing device's FCM token
    
    Args:
        db: Database session
        device: DeviceCreate object with device_uuid and fcm_token
        
    Returns:
        Device: The registered/updated device
        
    Raises:
        Exception: If database operation fails
    """
    try:
        # Check if device with same UUID already exists
        existing_device = db.query(Device).filter(Device.device_uuid == device.device_uuid).first()
        
        if existing_device:
            # Update existing device's FCM token and activate it
            existing_device.fcm_token = device.fcm_token
            existing_device.is_active = True
            db.commit()
            db.refresh(existing_device)
            logger.info(f"Updated existing device: {device.device_uuid}")
            return existing_device
        
        # Create new device
        new_device = Device(
            device_uuid=device.device_uuid,
            fcm_token=device.fcm_token
        )
        db.add(new_device)
        db.commit()
        db.refresh(new_device)
        logger.info(f"Registered new device: {device.device_uuid}")
        return new_device
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to register device {device.device_uuid}: {str(e)}")
        raise

def get_active_devices(db: Session) -> List[Device]:
    """
    Get all active devices
    
    Args:
        db: Database session
        
    Returns:
        List[Device]: List of active devices
    """
    return db.query(Device).filter(Device.is_active == True).all()

def get_device_by_uuid(db: Session, device_uuid: str) -> Optional[Device]:
    """
    Get a specific device by UUID
    
    Args:
        db: Database session
        device_uuid: Device UUID to search for
        
    Returns:
        Device or None: The device if found, None otherwise
    """
    return db.query(Device).filter(Device.device_uuid == device_uuid).first()

def deactivate_device(db: Session, device_uuid: str) -> bool:
    """
    Deactivate a device (set is_active to False)
    
    Args:
        db: Database session
        device_uuid: Device UUID to deactivate
        
    Returns:
        bool: True if device was deactivated, False if not found
    """
    device = db.query(Device).filter(Device.device_uuid == device_uuid).first()
    if device:
        device.is_active = False
        db.commit()
        logger.info(f"Deactivated device: {device_uuid}")
        return True
    return False

def get_device_tokens(db: Session, active_only: bool = True) -> List[str]:
    """
    Get FCM tokens for devices
    
    Args:
        db: Database session
        active_only: If True, return only active devices' tokens
        
    Returns:
        List[str]: List of FCM tokens
    """
    query = db.query(Device.fcm_token)
    if active_only:
        query = query.filter(Device.is_active == True)
    
    return [token[0] for token in query.all()]