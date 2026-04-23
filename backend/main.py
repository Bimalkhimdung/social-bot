"""FastAPI application entry point."""

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import init_db
from scheduler import start_scheduler, stop_scheduler
from routes import auth, sources, scraper, queue, posts, settings as settings_route, ws_logs, daily
from routes.ws_logs import install_ws_log_handler

settings = get_settings()

# -- Logging setup --
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("nepsebot")


# -- Lifespan --
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting NEPSE Bot backend...")
    await init_db()
    await _seed_default_sources()
    install_ws_log_handler()
    await start_scheduler()
    
    from database import AsyncSessionLocal
    from publisher.telegram import telegram_bot
    async with AsyncSessionLocal() as db:
        await telegram_bot.set_webhook(db)
    
    yield
    stop_scheduler()
    logger.info("Backend shutdown complete.")


app = FastAPI(
    title="NEPSE Facebook Auto-Poster Bot",
    version="1.0.0",
    description="Auto-scrape NEPSE news and post to Facebook Page.",
    lifespan=lifespan,
)

# -- CORS --
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Routers --
app.include_router(auth.router)
app.include_router(sources.router)
app.include_router(scraper.router)
app.include_router(queue.router)
app.include_router(posts.router)
app.include_router(settings_route.router)
app.include_router(ws_logs.router)
app.include_router(daily.router)

from routes import telegram, analytics
app.include_router(telegram.router, prefix="/api/telegram", tags=["telegram"])
app.include_router(analytics.router, tags=["analytics"])


# -- Health check --
@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "version": "1.0.0"}


# -- Stats endpoint for dashboard --
@app.get("/api/stats", tags=["stats"])
async def stats():
    from database import AsyncSessionLocal
    from models.post import Post, PostStatus
    from models.article import Article
    from scheduler import scheduler, _scraper_running
    from sqlalchemy import select, func
    from datetime import datetime

    async with AsyncSessionLocal() as db:
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)

        posts_today = await db.scalar(
            select(func.count(Post.id)).where(
                Post.status == PostStatus.posted,
                Post.posted_at >= today_start,
            )
        )
        pending_count = await db.scalar(
            select(func.count(Post.id)).where(Post.status == PostStatus.pending)
        )
        total_articles = await db.scalar(select(func.count(Article.id)))

        # Auto-approved stats
        auto_approved_count = await db.scalar(
            select(func.count(Post.id)).where(Post.is_auto_approved == True)
        )
        
        recent_auto_posts_res = await db.execute(
            select(Article.title, Post.posted_at)
            .join(Article, Post.article_id == Article.id)
            .where(Post.is_auto_approved == True, Post.status == PostStatus.posted)
            .order_by(Post.posted_at.desc())
            .limit(3)
        )
        recent_auto_posts = [
            {"title": row[0], "posted_at": row[1].isoformat() + "Z" if row[1] else None}
            for row in recent_auto_posts_res
        ]

        last_post_result = await db.execute(
            select(Post.posted_at).where(Post.status == PostStatus.posted)
            .order_by(Post.posted_at.desc()).limit(1)
        )
        last_post_at = last_post_result.scalar()

        # Dynamic SchedulerBar data
        from models.source import Source
        active_sources_res = await db.execute(select(Source.name).where(Source.is_active == True))
        active_sources = [r[0] for r in active_sources_res]

        from scheduler import scheduler as aps
        scrape_job = aps.get_job("scrape_job")
        next_scrape_at = None
        if scrape_job and scrape_job.next_run_time:
            nxt = scrape_job.next_run_time
            # Ensure it's ISO and ends with Z if it's naive (usually APScheduler uses aware UTC)
            val = nxt.isoformat()
            if "+" not in val and "Z" not in val:
                val += "Z"
            next_scrape_at = val

    return {
        "posts_today": posts_today or 0,
        "pending_count": pending_count or 0,
        "total_articles": total_articles or 0,
        "auto_approved_count": auto_approved_count or 0,
        "recent_auto_posts": recent_auto_posts,
        "last_post_at": last_post_at.isoformat() + "Z" if last_post_at else None,
        "scraper_running": _scraper_running,
        "scheduler_running": scheduler.running,
        "active_sources": active_sources,
        "next_scrape_at": next_scrape_at,
    }




# -- Seed default sources on first run --
async def _seed_default_sources():
    from database import AsyncSessionLocal
    from models.source import Source
    from scraper.sources import DEFAULT_SOURCES
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Source))
        existing = result.scalars().all()
        if existing:
            return  # Already seeded

        for cfg in DEFAULT_SOURCES:
            source = Source(
                name=cfg["name"],
                url=cfg["url"],
                source_type=cfg["source_type"],
                selector_config=json.dumps(cfg["selector_config"]),
                is_active=cfg["is_active"],
            )
            db.add(source)
        await db.commit()
        logger.info(f"Seeded {len(DEFAULT_SOURCES)} default sources")
