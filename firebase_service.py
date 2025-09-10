import firebase_admin
from firebase_admin import credentials, messaging
import os
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class FirebaseService:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_firebase()
            self._initialized = True
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            firebase_admin.get_app()
            logger.info("Firebase already initialized")
        except ValueError:
            # Firebase not initialized, so initialize it
            firebase_credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
                
            if firebase_credentials_json:
                # Use service account key JSON string (for Railway/Heroku deployment)
                try:
                    service_account_info = json.loads(firebase_credentials_json)
                    cred = credentials.Certificate(service_account_info)
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase initialized with credentials JSON")
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid Firebase credentials JSON: {e}")
                    raise
                    
            else:
                logger.error("No Firebase credentials found. Set FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON")
                raise ValueError("Firebase credentials not configured")
    
    async def send_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send a push notification to a single device
        
        Args:
            token: FCM registration token
            title: Notification title
            body: Notification body
            data: Optional additional data payload
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                token=token,
                data=data or {}
            )
            
            response = messaging.send(message)
            logger.info(f"Successfully sent message: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification to {token}: {str(e)}")
            return False
    
    async def send_multicast_notification(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> Dict[str, int]:
        """
        Send a push notification to multiple devices
        
        Args:
            tokens: List of FCM registration tokens
            title: Notification title
            body: Notification body
            data: Optional additional data payload
            
        Returns:
            dict: Summary with success_count, failure_count, and failed_tokens
        """
        if not tokens:
            return {"success_count": 0, "failure_count": 0, "failed_tokens": []}
        
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                tokens=tokens,
                data=data or {}
            )
            
            # Use send_each_for_multicast (recommended method)
            if hasattr(messaging, 'send_each_for_multicast'):
                response = messaging.send_each_for_multicast(message)
                logger.info("Used send_each_for_multicast method")
            else:
                logger.error("send_each_for_multicast not available, falling back to individual sends")
                return await self._send_individual_notifications(tokens, title, body, data)
            
            failed_tokens = []
            if response.failure_count > 0:
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        failed_tokens.append(tokens[idx])
                        logger.warning(f"Failed to send to token {tokens[idx]}: {resp.exception}")
            
            logger.info(f"Multicast notification sent. Success: {response.success_count}, Failed: {response.failure_count}")
            
            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "failed_tokens": failed_tokens
            }
            
        except Exception as e:
            logger.error(f"Error sending multicast notification: {str(e)}")
            return {
                "success_count": 0,
                "failure_count": len(tokens),
                "failed_tokens": tokens
            }
    
    async def send_topic_notification(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send a push notification to a topic
        
        Args:
            topic: Topic name
            title: Notification title
            body: Notification body
            data: Optional additional data payload
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                topic=topic,
                data=data or {}
            )
            
            response = messaging.send(message)
            logger.info(f"Successfully sent topic message to {topic}: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending topic notification to {topic}: {str(e)}")
            return False
    
    async def _send_individual_notifications(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> Dict[str, int]:
        """
        Fallback method to send notifications individually when multicast is not available
        """
        success_count = 0
        failed_tokens = []
        
        for token in tokens:
            success = await self.send_notification(token, title, body, data)
            if success:
                success_count += 1
            else:
                failed_tokens.append(token)
        
        return {
            "success_count": success_count,
            "failure_count": len(failed_tokens),
            "failed_tokens": failed_tokens
        }

# Singleton instance
firebase_service = FirebaseService()