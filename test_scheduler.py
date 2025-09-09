#!/usr/bin/env python3
"""
Test script for the scheduled news analysis system.
Run this to test the complete workflow without waiting for scheduled time.
"""

import asyncio
import logging
from scheduler_service import news_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_workflow():
    """Test the complete workflow"""
    print("🧪 Testing Complete News Analysis Workflow")
    print("=" * 50)
    
    try:
        # Test the daily news analysis task
        print("📊 Running news analysis task...")
        await news_scheduler.daily_news_analysis_task()
        print("✅ News analysis workflow completed successfully!")
        
    except Exception as e:
        print(f"❌ Workflow failed: {str(e)}")
        import traceback
        traceback.print_exc()

def test_scheduler_setup():
    """Test scheduler configuration"""
    print("\n🕐 Testing Scheduler Setup")
    print("=" * 30)
    
    # Start scheduler
    news_scheduler.start_scheduler()
    
    # Check status
    status = news_scheduler.get_scheduler_status()
    print(f"Scheduler Status: {status['status']}")
    
    if status['jobs']:
        for job in status['jobs']:
            print(f"Job: {job['name']}")
            print(f"  ID: {job['id']}")
            print(f"  Next Run: {job['next_run_time']}")
            print(f"  Trigger: {job['trigger']}")
    
    # Stop scheduler
    news_scheduler.stop_scheduler()
    print("✅ Scheduler test completed!")

async def main():
    """Main test function"""
    print("🚀 Starting News Analysis System Tests\n")
    
    # Test 1: Scheduler setup
    test_scheduler_setup()
    
    # Test 2: Complete workflow
    await test_workflow()
    
    print("\n✨ All tests completed!")
    print("\nTo test with real scheduling:")
    print("1. Start your FastAPI server: uv run python main.py")
    print("2. Check scheduler status: GET /admin/scheduler/status")
    print("3. Trigger manual run: POST /admin/scheduler/run-now")
    print("4. The scheduler will automatically run daily at 5 PM KST")

if __name__ == "__main__":
    asyncio.run(main())