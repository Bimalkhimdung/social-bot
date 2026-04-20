"""
Analytics routes for dashboard visualizations.
"""

from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.post import Post, PostStatus

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/performance")
async def get_performance_stats(db: Annotated[AsyncSession, Depends(get_db)]):
    """
    Return scraped vs approved counts for the last 7 days.
    """
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    
    # We want a list of days: { day: 'MON', scraped: 10, approved: 5 }
    # Group by the date part of created_at
    result = await db.execute(
        select(
            func.date(Post.created_at).label("date"),
            func.count(Post.id).label("scraped"),
            func.count(Post.id).filter(or_(Post.status == PostStatus.approved, Post.status == PostStatus.posted)).label("approved")
        )
        .where(Post.created_at >= seven_days_ago)
        .group_by(func.date(Post.created_at))
        .order_by(func.date(Post.created_at).asc())
    )
    
    rows = result.all()
    
    days_map = {0: "MON", 1: "TUE", 2: "WED", 3: "THU", 4: "FRI", 5: "SAT", 6: "SUN"}
    
    data = []
    for row in rows:
        # row.date is a date object
        day_str = days_map[row.date.weekday()]
        data.append({
            "day": day_str,
            "scraped": row.scraped,
            "approved": row.approved,
            "raw_date": row.date.isoformat()
        })
        
    # If we have fewer than 7 days, they might be missing. 
    # But for a simple MVP, the above is fine. 
    # If missing days are needed, we can backfill with zeros.
    
    return data
