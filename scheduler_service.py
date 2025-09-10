import asyncio
import logging
import json
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from crew_financial_news_analysis import FinancialNewsAnalysis
from news_service import save_news_analysis
from device_service import get_device_tokens
from firebase_service import firebase_service
from database import SessionLocal
from models import NewsEntity

logger = logging.getLogger(__name__)

class NewsSchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.korea_tz = pytz.timezone('Asia/Seoul')
        
    async def daily_news_analysis_task(self):
        """
        Daily task that:
        1. Runs FinancialNewsAnalysis
        2. Saves results to database
        3. Sends push notifications to all users
        """
        logger.info("Starting daily news analysis task...")
        db = SessionLocal()
        
        try:
            # Step 1: Run financial news analysis
            logger.info("Running financial news analysis...")
            analysis = FinancialNewsAnalysis()
            result = analysis.crew().kickoff()
            
            if not result:
                logger.warning("No news analysis results received")
                return
                
            # Extract the actual data from CrewOutput object
            if hasattr(result, 'raw'):
                raw_data = result.raw
            elif hasattr(result, 'output'):
                raw_data = result.output
            else:
                raw_data = result
            
            # Parse JSON string to list of dictionaries if needed
            if isinstance(raw_data, str):
                try:
                    parsed_data = json.loads(raw_data)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON from crew output: {raw_data}")
                    return
            else:
                parsed_data = raw_data
            
            # Convert to NewsEntity objects
            news_entities = []
            if isinstance(parsed_data, list):
                for item in parsed_data:
                    if isinstance(item, dict):
                        news_entity = NewsEntity(
                            title=item.get('title', ''),
                            summarize=item.get('summarize', ''),
                            url=item.get('url', ''),
                            published_date=item.get('published_date', ''),
                            score=item.get('score', 0),
                            tickers=item.get('tickers', [])
                        )
                        news_entities.append(news_entity)
            
            if not news_entities:
                logger.warning("No valid news entities found after parsing")
                return
                
            logger.info(f"Analysis completed. Processing {len(news_entities)} news items...")
            
            # Step 2: Save to database
            logger.info("Saving news analysis to database...")
            save_result = save_news_analysis(news_entities)
            logger.info(f"Database save completed: {save_result}")
            
            # Only send notifications if we saved new items
            if save_result['saved'] > 0:
                # Step 3: Send push notifications to all users
                logger.info("Sending push notifications to users...")
                await self._send_news_update_notifications(save_result)
            else:
                logger.info("No new news items saved, skipping notifications")
                
        except Exception as e:
            logger.error(f"Daily news analysis task failed: {str(e)}", exc_info=True)
        finally:
            db.close()
            
    async def _send_news_update_notifications(self, save_result: dict):
        """Send push notifications about news updates to all active devices"""
        db = SessionLocal()
        
        try:
            # Get all active device tokens
            tokens = get_device_tokens(db, active_only=True)
            
            if not tokens:
                logger.info("No active device tokens found for notifications")
                return
                
            logger.info(f"Sending notifications to {len(tokens)} devices...")
            
            # Prepare notification content
            saved_count = save_result['saved']
            title = "📈 Financial News Update"
            
            if saved_count == 1:
                body = "1 new market-moving news analysis is available!"
            else:
                body = f"{saved_count} new market-moving news analyses are available!"
            
            # Additional data payload
            data = {
                "type": "news_update",
                "saved_count": str(saved_count),
                "timestamp": datetime.now(self.korea_tz).isoformat()
            }
            
            # Send multicast notification
            notification_result = await firebase_service.send_multicast_notification(
                tokens=tokens,
                title=title,
                body=body,
                data=data
            )
            
            logger.info(f"Notification results: {notification_result}")
            
            # Log failed tokens for cleanup (optional)
            if notification_result['failed_tokens']:
                logger.warning(f"Failed to send to {len(notification_result['failed_tokens'])} devices")
                # TODO: Could implement logic to deactivate failed tokens
                
        except Exception as e:
            logger.error(f"Failed to send news update notifications: {str(e)}", exc_info=True)
        finally:
            db.close()
    
    def start_scheduler(self):
        """Start the scheduler with daily 5 PM and 10 PM KST tasks"""
        try:
            # Schedule daily task at 5 PM Korea time
            self.scheduler.add_job(
                self.daily_news_analysis_task,
                trigger=CronTrigger(
                    hour=17,  # 5 PM
                    minute=0,
                    timezone=self.korea_tz
                ),
                id='daily_news_analysis_5pm',
                name='Daily Financial News Analysis (5 PM)',
                replace_existing=True
            )
            
            # Schedule daily task at 10 PM Korea time
            self.scheduler.add_job(
                self.daily_news_analysis_task,
                trigger=CronTrigger(
                    hour=22,  # 10 PM
                    minute=0,
                    timezone=self.korea_tz
                ),
                id='daily_news_analysis_10pm',
                name='Daily Financial News Analysis (10 PM)',
                replace_existing=True
            )
            
            # Add a test job for immediate testing (optional)
            # Uncomment the lines below if you want to test immediately
            # self.scheduler.add_job(
            #     self.daily_news_analysis_task,
            #     trigger='date',
            #     run_date=datetime.now(self.korea_tz),
            #     id='test_news_analysis',
            #     name='Test News Analysis'
            # )
            
            self.scheduler.start()
            logger.info("News scheduler started successfully")
            logger.info(f"Daily news analysis scheduled for 5:00 PM and 10:00 PM Korea time")
            
            # Log next run times
            job_5pm = self.scheduler.get_job('daily_news_analysis_5pm')
            job_10pm = self.scheduler.get_job('daily_news_analysis_10pm')
            if job_5pm:
                next_run_5pm = job_5pm.next_run_time
                logger.info(f"Next 5 PM run: {next_run_5pm}")
            if job_10pm:
                next_run_10pm = job_10pm.next_run_time
                logger.info(f"Next 10 PM run: {next_run_10pm}")
                
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}", exc_info=True)
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("News scheduler stopped")
    
    def get_scheduler_status(self):
        """Get current scheduler status and job info"""
        if not self.scheduler.running:
            return {"status": "stopped", "jobs": []}
        
        jobs_info = []
        for job in self.scheduler.get_jobs():
            jobs_info.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "status": "running",
            "jobs": jobs_info
        }

# Singleton instance
news_scheduler = NewsSchedulerService()