from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import NewsAnalysis, NewsEntity
from database import SessionLocal
from typing import List
import logging

logger = logging.getLogger(__name__)

def save_news_analysis(news_list: List[NewsEntity]) -> dict:
    """
    Save news analysis results to database with duplicate prevention.
    
    Args:
        news_list: List of NewsEntity objects from FinancialNewsAnalysis
        
    Returns:
        dict: Summary of save operation with counts of saved, skipped, and failed items
    """
    db = SessionLocal()
    saved_count = 0
    skipped_count = 0
    failed_count = 0
    
    try:
        for news_item in news_list:
            try:
                # Check if news with same URL already exists
                existing_news = db.query(NewsAnalysis).filter(NewsAnalysis.url == news_item.url).first()
                
                if existing_news:
                    logger.info(f"Skipping duplicate news: {news_item.url}")
                    skipped_count += 1
                    continue
                
                # Create new NewsAnalysis record
                db_news = NewsAnalysis(
                    title=news_item.title,
                    summarize=news_item.summarize,
                    url=news_item.url,
                    published_date=news_item.published_date,
                    score=news_item.score,
                    tickers=news_item.tickers
                )
                
                db.add(db_news)
                db.commit()
                db.refresh(db_news)
                
                logger.info(f"Saved news analysis: {news_item.url}")
                saved_count += 1
                
            except IntegrityError as e:
                # Handle unique constraint violation (duplicate URL)
                db.rollback()
                logger.warning(f"Duplicate URL detected, skipping: {news_item.url}")
                skipped_count += 1
                
            except Exception as e:
                # Handle other database errors
                db.rollback()
                logger.error(f"Failed to save news analysis for {news_item.url}: {str(e)}")
                failed_count += 1
                
    finally:
        db.close()
    
    result = {
        "total_processed": len(news_list),
        "saved": saved_count,
        "skipped_duplicates": skipped_count,
        "failed": failed_count
    }
    
    logger.info(f"News analysis save operation completed: {result}")
    return result

def get_recent_news_analysis(db: Session, limit: int = 50) -> List[NewsAnalysis]:
    """
    Retrieve recent news analysis from database.
    
    Args:
        db: Database session
        limit: Maximum number of records to return
        
    Returns:
        List of NewsAnalysis records ordered by creation time (newest first)
    """
    return db.query(NewsAnalysis).order_by(NewsAnalysis.created_at.desc()).limit(limit).all()

def get_news_by_score_range(db: Session, min_score: int = None, max_score: int = None) -> List[NewsAnalysis]:
    """
    Retrieve news analysis filtered by score range.
    
    Args:
        db: Database session
        min_score: Minimum score filter (inclusive)
        max_score: Maximum score filter (inclusive)
        
    Returns:
        List of NewsAnalysis records matching score criteria
    """
    query = db.query(NewsAnalysis)
    
    if min_score is not None:
        query = query.filter(NewsAnalysis.score >= min_score)
    if max_score is not None:
        query = query.filter(NewsAnalysis.score <= max_score)
        
    return query.order_by(NewsAnalysis.created_at.desc()).all()

def get_news_feed_with_cursor(
    db: Session,
    cursor_id: int = None,
    limit: int = 20,
    min_score: int = None,
    max_score: int = None
) -> dict:
    """
    Get news feed using cursor-based pagination for infinite scroll.
    
    Args:
        db: Database session
        cursor_id: Last news ID from previous request (for next page)
        limit: Number of items to return
        min_score: Minimum score filter (inclusive)
        max_score: Maximum score filter (inclusive)
        
    Returns:
        dict: Cursor-based paginated news data
        {
            "items": List[NewsAnalysis],
            "next_cursor_id": int or None,
            "has_more": bool,
            "limit": int
        }
    """
    # Build base query
    query = db.query(NewsAnalysis)
    
    # Apply score filters
    if min_score is not None:
        query = query.filter(NewsAnalysis.score >= min_score)
    if max_score is not None:
        query = query.filter(NewsAnalysis.score <= max_score)
    
    # Apply cursor filter (get items with ID less than cursor for descending order)
    if cursor_id is not None:
        query = query.filter(NewsAnalysis.id < cursor_id)
    
    # Order by ID descending (newest first) and get one extra to check if there's more
    items = query.order_by(NewsAnalysis.id.desc()).limit(limit + 1).all()
    
    # Check if there are more items
    has_more = len(items) > limit
    if has_more:
        items = items[:limit]  # Remove the extra item
    
    # Get next cursor (ID of last item)
    next_cursor_id = items[-1].id if items and has_more else None
    
    # Convert datetime objects to strings for API response
    serialized_items = []
    for item in items:
        item_dict = {
            "id": item.id,
            "title": item.title,
            "summarize": item.summarize,
            "url": item.url,
            "published_date": item.published_date.isoformat() if hasattr(item.published_date, 'isoformat') else item.published_date,
            "score": item.score,
            "tickers": item.tickers,
            "created_at": item.created_at.isoformat()
        }
        serialized_items.append(item_dict)
    
    return {
        "items": serialized_items,
        "next_cursor_id": next_cursor_id,
        "has_more": has_more,
        "limit": limit
    }

def get_news_by_id(db: Session, news_id: int) -> NewsAnalysis:
    """
    Retrieve a single news item by its ID.

    Args:
        db: Database session
        news_id: ID of the news item to retrieve

    Returns:
        NewsAnalysis record or None if not found
    """
    return db.query(NewsAnalysis).filter(NewsAnalysis.id == news_id).first()

def clear_all_news_analysis(db: Session) -> dict:
    """
    Delete all news analysis records from the database.
    Used for cleaning up fake or test data.

    Args:
        db: Database session

    Returns:
        dict: Summary of the deletion operation
    """
    try:
        # Count existing records before deletion
        count_before = db.query(NewsAnalysis).count()

        # Delete all news analysis records
        deleted_count = db.query(NewsAnalysis).delete()
        db.commit()

        # Verify deletion
        count_after = db.query(NewsAnalysis).count()

        result = {
            "records_deleted": deleted_count,
            "count_before": count_before,
            "count_after": count_after,
            "status": "success"
        }

        logger.info(f"Cleared all news analysis data: {result}")
        return result

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to clear news analysis data: {str(e)}")
        raise e