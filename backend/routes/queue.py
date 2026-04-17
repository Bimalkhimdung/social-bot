"""Post queue management routes."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.post import Post, PostStatus
from models.article import Article
from models.source import Source
from routes.auth import get_current_user

router = APIRouter(prefix="/api/queue", tags=["queue"])


class PostEditBody(BaseModel):
    caption: str | None = None
    scheduled_at: str | None = None  # ISO datetime string


def _post_out(post: Post, article: Article, source: Source) -> dict:
    return {
        "id": post.id,
        "status": post.status.value,
        "caption": post.caption,
        "scheduled_at": post.scheduled_at.isoformat() if post.scheduled_at else None,
        "posted_at": post.posted_at.isoformat() if post.posted_at else None,
        "fb_post_id": post.fb_post_id,
        "created_at": post.created_at.isoformat(),
        "article": {
            "id": article.id,
            "title": article.title,
            "summary": article.summary,
            "image_url": article.image_url,
            "article_url": article.article_url,
            "keywords": article.keywords_list,
            "scraped_at": article.scraped_at.isoformat(),
            "source_name": source.name,
            "source_label": article.source_label,
        },
    }


async def _fetch_post_row(post_id: int, db: AsyncSession):
    result = await db.execute(
        select(Post, Article, Source)
        .join(Article, Post.article_id == Article.id)
        .join(Source, Article.source_id == Source.id)
        .where(Post.id == post_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    return row


# ---------------------------------------------------------------------------
# Preview: generate card image and return it as JPEG
# ---------------------------------------------------------------------------

@router.get("/{post_id}/preview-card", response_class=Response)
async def preview_card(
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Generate and return the news card image (JPEG) for a given post.
    No authentication required so the frontend can load it in an <img> tag.
    Open directly in browser: GET /api/queue/{post_id}/preview-card
    """
    post, article, source = await _fetch_post_row(post_id, db)

    from image_card.generator import generate_news_card
    try:
        card_bytes = await generate_news_card(
            title=article.title,
            image_url=article.image_url,
            source_label=article.source_label or source.name,
            article_url=article.article_url,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Card generation failed: {exc}")

    return Response(
        content=card_bytes,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-cache"},
    )


@router.get("")
async def list_queue(
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = None,
    page: int = 1,
    limit: int = 20,
):
    query = (
        select(Post, Article, Source)
        .join(Article, Post.article_id == Article.id)
        .join(Source, Article.source_id == Source.id)
    )
    if status:
        try:
            filter_status = PostStatus(status)
            query = query.where(Post.status == filter_status)
        except ValueError:
            pass

    query = query.order_by(Post.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    rows = result.all()
    return [_post_out(p, a, s) for p, a, s in rows]


@router.put("/{post_id}/approve")
async def approve_post(
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[str, Depends(get_current_user)],
):
    post, article, source = await _fetch_post_row(post_id, db)
    post.status = PostStatus.approved
    await db.commit()
    return _post_out(post, article, source)


@router.put("/{post_id}/reject")
async def reject_post(
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[str, Depends(get_current_user)],
):
    post, article, source = await _fetch_post_row(post_id, db)
    await db.delete(post)
    await db.commit()
    return {"deleted": True, "id": post_id}


@router.put("/{post_id}")
async def edit_post(
    post_id: int,
    body: PostEditBody,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[str, Depends(get_current_user)],
):
    post, article, source = await _fetch_post_row(post_id, db)
    if body.caption is not None:
        post.caption = body.caption
    if body.scheduled_at is not None:
        post.scheduled_at = datetime.fromisoformat(body.scheduled_at)
    await db.commit()
    return _post_out(post, article, source)


@router.post("/{post_id}/publish-now")
async def publish_now(
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[str, Depends(get_current_user)],
):
    from publisher.facebook import publisher, build_caption

    post, article, source = await _fetch_post_row(post_id, db)

    caption = post.caption or await build_caption(
        db,
        title=article.title,
        source_name=source.name,
        article_url=article.article_url,
        keywords=article.keywords_list,
    )

    # ── Generate image card manually ────────────────────────────────
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
        print(f"Manual card generation failed: {exc}")

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

    return {**_post_out(post, article, source), "dry_run": not publisher.is_configured}
