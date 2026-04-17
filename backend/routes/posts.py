"""Post history routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.post import Post, PostStatus
from models.article import Article
from models.source import Source

router = APIRouter(prefix="/api/posts", tags=["posts"])


def _post_out(post: Post, article: Article, source: Source) -> dict:
    return {
        "id": post.id,
        "status": post.status.value,
        "caption": post.caption,
        "posted_at": post.posted_at.isoformat() if post.posted_at else None,
        "fb_post_id": post.fb_post_id,
        "created_at": post.created_at.isoformat(),
        "article": {
            "id": article.id,
            "title": article.title,
            "summary": article.summary,
            "image_url": article.image_url,
            "article_url": article.article_url,
            "source_name": source.name,
        },
    }


@router.get("")
async def list_posts(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    limit: int = 20,
):
    result = await db.execute(
        select(Post, Article, Source)
        .join(Article, Post.article_id == Article.id)
        .join(Source, Article.source_id == Source.id)
        .where(Post.status == PostStatus.posted)
        .order_by(Post.posted_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    rows = result.all()
    return [_post_out(p, a, s) for p, a, s in rows]


@router.get("/{post_id}")
async def get_post(
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Post, Article, Source)
        .join(Article, Post.article_id == Article.id)
        .join(Source, Article.source_id == Source.id)
        .where(Post.id == post_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    return _post_out(*row)
