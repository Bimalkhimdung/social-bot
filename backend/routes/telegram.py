"""
Telegram Webhook Route
Receives callbacks from inline buttons (Approve/Reject).
"""

import logging
from typing import Any
from fastapi import APIRouter, Request, BackgroundTasks
from sqlalchemy import select
from datetime import datetime

from database import AsyncSessionLocal
from models.post import Post, PostStatus
from models.article import Article
from models.source import Source
from publisher.telegram import telegram_bot
from publisher.facebook import publisher, build_caption
from config import get_settings

logger = logging.getLogger("nepsebot.telegram.route")
router = APIRouter()
settings = get_settings()

async def publish_approved_post(post_id: int):
    """Background task to instantly publish the approved post to Facebook."""
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Post, Article, Source)
                .join(Article, Post.article_id == Article.id)
                .join(Source, Article.source_id == Source.id)
                .where(Post.id == post_id)
            )
            row = result.first()
            if not row:
                return
            
            post, article, source = row
            if post.status != PostStatus.approved:
                logger.warning(f"Post {post_id} is not approved, aborting instant publish.")
                return

            logger.info(f"Instant publishing approved post {post_id}...")

            caption = post.caption or await build_caption(
                db,
                title=article.title,
                source_name=source.name,
                article_url=article.article_url,
                keywords=article.keywords_list,
            )

            # Generate image card
            photo_id = None
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
            logger.info(f"Instant publish complete for post {post_id}")
            
    except Exception as exc:
        logger.error(f"Error in background publish: {exc}", exc_info=True)


@router.post("/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive updates from Telegram."""
    try:
        data = await request.json()
    except Exception:
        return {"status": "ok"}  # Ignore malformed payload

    if "callback_query" in data:
        callback_query = data["callback_query"]
        callback_id = callback_query.get("id")
        message = callback_query.get("message", {})
        message_id = message.get("message_id")
        cb_data = callback_query.get("data", "")
        
        if not cb_data:
            return {"status": "ok"}
            
        action, _, post_id_str = cb_data.partition("_")
        
        if action in ("approve", "reject") and post_id_str.isdigit():
            post_id = int(post_id_str)
            new_status = PostStatus.approved if action == "approve" else PostStatus.rejected
            
            # Update DB
            async with AsyncSessionLocal() as db:
                post = await db.get(Post, post_id)
                if post and post.status == PostStatus.pending:
                    post.status = new_status
                    await db.commit()
                    logger.info(f"Post {post_id} was {new_status.value} via Telegram.")
                    
                    # Update Telegram message to remove buttons and show confirmation
                    await telegram_bot.edit_message_status(db, message_id, post_id, new_status.value)
                    
                    # Answer callback query to stop loading spinner
                    await telegram_bot.answer_callback_query(db, callback_id, f"Post {new_status.value}!")
                    
                    # If approved, immediately publish
                    if new_status == PostStatus.approved:
                        background_tasks.add_task(publish_approved_post, post_id)
                else:
                    await answer_callback_query(callback_id, "Post already handled or not found.")

    return {"status": "ok"}
