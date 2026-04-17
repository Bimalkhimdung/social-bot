"""FastAPI application entry point."""

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import init_db
from scheduler import start_scheduler, stop_scheduler
from routes import auth, sources, scraper, queue, posts, settings as settings_route, ws_logs
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
    start_scheduler()
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

        last_post_result = await db.execute(
            select(Post.posted_at).where(Post.status == PostStatus.posted)
            .order_by(Post.posted_at.desc()).limit(1)
        )
        last_post_at = last_post_result.scalar()

    return {
        "posts_today": posts_today or 0,
        "pending_count": pending_count or 0,
        "total_articles": total_articles or 0,
        "last_post_at": last_post_at.isoformat() if last_post_at else None,
        "scraper_running": _scraper_running,
        "scheduler_running": scheduler.running,
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
