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
from datetime import datetime, time as dt_time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import AsyncSessionLocal

logger = logging.getLogger("nepsebot.scheduler")
settings = get_settings()

scheduler = AsyncIOScheduler(
    jobstores={"default": MemoryJobStore()},
    timezone="Asia/Kathmandu",
)

_scraper_running = False


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
    from sqlalchemy import select, func

    cfg = get_settings()
    now = datetime.now()
    current_hour = now.hour

    # Quiet hours check
    qs, qe = cfg.quiet_hours_start, cfg.quiet_hours_end
    if qs > qe:  # crosses midnight
        in_quiet = current_hour >= qs or current_hour < qe
    else:
        in_quiet = qs <= current_hour < qe

    if in_quiet:
        logger.info(f"Quiet hours active ({qs}:00–{qe}:00) — skipping publish")
        return

    async with AsyncSessionLocal() as db:
        # Count posts published today
        today_start = datetime(now.year, now.month, now.day)
        posted_today = await db.scalar(
            select(func.count(Post.id)).where(
                Post.status == PostStatus.posted,
                Post.posted_at >= today_start,
            )
        )

        if posted_today >= cfg.max_posts_per_day:
            logger.info(f"Max posts/day reached ({posted_today}/{cfg.max_posts_per_day}) — skipping")
            return

        # Get next approved post (optionally scheduled)
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

        # Build caption if not manually set
        caption = post.caption or build_caption(
            title=article.title,
            source_name=source.name,
            article_url=article.article_url,
            keywords=article.keywords_list,
        )

        # ── Generate image card ──────────────────────────────────────────
        photo_id: str | None = None
        try:
            from image_card.generator import generate_news_card
            card_bytes = await generate_news_card(
                title=article.title,
                image_url=article.image_url,
                source_label=article.source_label or source.name,
                article_url=article.article_url,
            )
            logger.info(f"Card generated ({len(card_bytes) // 1024} KB) for article id={article.id}")
            if publisher.is_configured:
                photo_id = await publisher.upload_photo(card_bytes)
        except Exception as exc:
            logger.warning(f"Card generation failed (will post without image): {exc}", exc_info=True)

        fb_post_id = publisher.publish(
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

def start_scheduler():
    interval = settings.scrape_interval_minutes

    scheduler.add_job(
        scrape_job,
        "interval",
        minutes=interval,
        id="scrape_job",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.add_job(
        publish_job,
        "interval",
        minutes=30,
        id="publish_job",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()
    logger.info(f"Scheduler started — scrape every {interval}min, publish every 30min")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
