"""
APScheduler setup.

Two persistent jobs:
  1. scrape_job  — runs every N minutes (default 30)
  2. publish_job — runs every 30 minutes, enforces max posts/day + quiet hours

Both jobs re-read their intervals from DB settings on each tick so changes
made in the dashboard take effect without a restart.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import AsyncSessionLocal
from models.settings import Setting

logger = logging.getLogger("nepsebot.scheduler")
settings = get_settings()

scheduler = AsyncIOScheduler(
    jobstores={"default": MemoryJobStore()},
    timezone="Asia/Kathmandu",
)

_scraper_running = False


async def _get_lived_settings(db: AsyncSession) -> dict[str, Any]:
    """Fetch interval and limits from database 'Setting' table."""
    keys = [
        "scrape_interval_minutes",
        "publish_interval_minutes",
        "max_posts_per_day",
        "quiet_hours_start",
        "quiet_hours_end",
        "auto_publish"
    ]
    result = await db.execute(select(Setting).where(Setting.key.in_(keys)))
    items = {s.key: s.value for s in result.scalars().all()}
    
    cfg = get_settings()
    
    # Helpers for safe parsing
    def _get_int(key, default):
        val = items.get(key)
        try:
            return int(val) if val is not None else default
        except (ValueError, TypeError):
            return default

    def _get_bool(key, default):
        val = items.get(key)
        if val is None: return default
        return str(val).lower() == "true"

    return {
        "scrape_interval_minutes": _get_int("scrape_interval_minutes", cfg.scrape_interval_minutes),
        "publish_interval_minutes": _get_int("publish_interval_minutes", cfg.publish_interval_minutes),
        "max_posts_per_day": _get_int("max_posts_per_day", cfg.max_posts_per_day),
        "quiet_hours_start": _get_int("quiet_hours_start", cfg.quiet_hours_start),
        "quiet_hours_end": _get_int("quiet_hours_end", cfg.quiet_hours_end),
        "auto_publish": _get_bool("auto_publish", cfg.auto_publish),
    }


# ---------------------------------------------------------------------------
# Job: scrape all sources
# ---------------------------------------------------------------------------

async def scrape_job():
    global _scraper_running
    if _scraper_running:
        logger.warning("Scrape already in progress — skipping tick")
        return
    _scraper_running = True
    logger.info("Scrape job started")
    
    try:
        from scraper.engine import scrape_all_sources
        async with AsyncSessionLocal() as db:
            # 1. Check for interval changes to reschedule next tick
            live = await _get_lived_settings(db)
            new_interval = live["scrape_interval_minutes"]
            
            job = scheduler.get_job("scrape_job")
            if job:
                # APScheduler stores interval as a timedelta with minutes
                current_minutes = job.trigger.interval.total_seconds() / 60
                if int(current_minutes) != new_interval:
                    logger.info(f"Rescheduling scrape_job: {int(current_minutes)}m -> {new_interval}m")
                    scheduler.reschedule_job("scrape_job", trigger="interval", minutes=new_interval)

            # 2. Perform scraping
            stats = await scrape_all_sources(db)
        logger.info(f"Scrape job done: {stats}")
    except Exception as exc:
        logger.error(f"Scrape job failed: {exc}", exc_info=True)
    finally:
        _scraper_running = False


# ---------------------------------------------------------------------------
# Job: publish approved posts
# ---------------------------------------------------------------------------

async def publish_job():
    from models.post import Post, PostStatus
    from models.article import Article
    from models.source import Source
    from publisher.facebook import publisher, build_caption
    from sqlalchemy import func

    async with AsyncSessionLocal() as db:
        # Load live settings
        live = await _get_lived_settings(db)
        
        # 0. Reschedule if interval changed
        new_interval = live["publish_interval_minutes"]
        job = scheduler.get_job("publish_job")
        if job:
            current_minutes = job.trigger.interval.total_seconds() / 60
            if int(current_minutes) != new_interval:
                logger.info(f"Rescheduling publish_job: {int(current_minutes)}m -> {new_interval}m")
                scheduler.reschedule_job("publish_job", trigger="interval", minutes=new_interval)

        # 1. Master toggle check
        if not live["auto_publish"]:
            logger.debug("Auto-publish is disabled in settings — skipping")
            return

        max_posts = live["max_posts_per_day"]
        qs = live["quiet_hours_start"]
        qe = live["quiet_hours_end"]

        now = datetime.now()
        current_hour = now.hour

        # Quiet hours check
        if qs > qe:  # crosses midnight
            in_quiet = current_hour >= qs or current_hour < qe
        else:
            in_quiet = qs <= current_hour < qe

        if in_quiet:
            logger.info(f"Quiet hours active ({qs}:00–{qe}:00) — skipping publish")
            return

        # Count posts published today
        today_start = datetime(now.year, now.month, now.day)
        posted_today = await db.scalar(
            select(func.count(Post.id)).where(
                Post.status == PostStatus.posted,
                Post.posted_at >= today_start,
            )
        )

        if posted_today >= max_posts:
            logger.info(f"Max posts/day reached ({posted_today}/{max_posts}) — skipping")
            return

        # Get next approved post
        result = await db.execute(
            select(Post, Article, Source)
            .join(Article, Post.article_id == Article.id)
            .join(Source, Article.source_id == Source.id)
            .where(Post.status == PostStatus.approved)
            .where(
                (Post.scheduled_at == None) | (Post.scheduled_at <= now)  # noqa: E711
            )
            .order_by(Post.created_at.asc())
            .limit(1)
        )
        row = result.first()

        if not row:
            logger.debug("No approved posts to publish")
            return

        post, article, source = row

        # Build caption
        caption = post.caption or await build_caption(
            db,
            title=article.title,
            source_name=source.name,
            article_url=article.article_url,
            keywords=article.keywords_list,
        )

        # Generate card
        photo_id: str | None = None
        try:
            from image_card.generator import generate_news_card
            card_bytes = await generate_news_card(
                title=article.title,
                image_url=article.image_url,
                source_label=article.source_label or source.name,
                article_url=article.article_url,
            )
            if publisher.is_configured:
                photo_id = await publisher.upload_photo(db, card_bytes)
        except Exception as exc:
            logger.warning(f"Card generation failed: {exc}", exc_info=True)

        fb_post_id = await publisher.publish(
            db,
            title=article.title,
            article_url=article.article_url,
            caption=caption,
            image_url=article.image_url,
            photo_id=photo_id,
            dry_run=not publisher.is_configured,
        )

        post.status = PostStatus.posted
        post.posted_at = datetime.utcnow()
        post.caption = caption
        if fb_post_id:
            post.fb_post_id = fb_post_id

        await db.commit()
        logger.info(f"Published post id={post.id}, article='{article.title[:60]}'")


# ---------------------------------------------------------------------------
# Start / stop
# ---------------------------------------------------------------------------

async def start_scheduler():
    """Start the scheduler, initializing intervals from DB if available."""
    async with AsyncSessionLocal() as db:
        live = await _get_lived_settings(db)
        scrape_int = live["scrape_interval_minutes"]
        publish_int = live["publish_interval_minutes"]

    scheduler.add_job(
        scrape_job,
        "interval",
        minutes=scrape_int,
        id="scrape_job",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.add_job(
        publish_job,
        "interval",
        minutes=publish_int,
        id="publish_job",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()
    logger.info(f"Scheduler started — scrape every {scrape_int}m, publish every {publish_int}m")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

