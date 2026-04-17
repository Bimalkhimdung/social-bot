#!/usr/bin/env python3
"""
Standalone card preview script — run directly from backend/ directory.

Usage:
    python test_card.py                          # uses built-in sample article
    python test_card.py --title "your title"     # custom title
    python test_card.py --url https://...        # custom article URL + image
    python test_card.py --post-id 5              # generate from a DB post
    python test_card.py --open                   # open in browser after generating
"""

import argparse
import asyncio
import subprocess
import sys
from pathlib import Path


async def from_sample(title: str, image_url: str, source: str, article_url: str) -> bytes:
    from image_card.generator import generate_news_card
    return await generate_news_card(
        title=title,
        image_url=image_url,
        source_label=source,
        article_url=article_url,
    )


async def from_db(post_id: int) -> bytes:
    """Pull article data from PostgreSQL and generate its card."""
    from database import AsyncSessionLocal
    from models.post import Post
    from models.article import Article
    from models.source import Source
    from sqlalchemy import select
    from image_card.generator import generate_news_card

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Post, Article, Source)
            .join(Article, Post.article_id == Article.id)
            .join(Source, Article.source_id == Source.id)
            .where(Post.id == post_id)
        )
        row = result.first()
        if not row:
            print(f"❌ Post {post_id} not found in database.")
            sys.exit(1)
        post, article, source = row
        print(f"📰 Article  : {article.title}")
        print(f"🖼  Image    : {article.image_url or '(none)'}")
        print(f"🏷  Source   : {article.source_label or source.name}")
        print(f"🔗 URL      : {article.article_url}")
        return await generate_news_card(
            title=article.title,
            image_url=article.image_url,
            source_label=article.source_label or source.name,
            article_url=article.article_url,
        )


async def from_latest_db() -> bytes:
    """Pull the most recently scraped article from the DB."""
    from database import AsyncSessionLocal
    from models.post import Post
    from models.article import Article
    from models.source import Source
    from sqlalchemy import select
    from image_card.generator import generate_news_card

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Post, Article, Source)
            .join(Article, Post.article_id == Article.id)
            .join(Source, Article.source_id == Source.id)
            .order_by(Post.created_at.desc())
            .limit(1)
        )
        row = result.first()
        if not row:
            return None
        post, article, source = row
        print(f"📰 Article  : {article.title}")
        print(f"🖼  Image    : {article.image_url or '(none)'}")
        print(f"🏷  Source   : {article.source_label or source.name}")
        print(f"🔗 URL      : {article.article_url}")
        return await generate_news_card(
            title=article.title,
            image_url=article.image_url,
            source_label=article.source_label or source.name,
            article_url=article.article_url,
        )


SAMPLE = {
    "title": "धितोपत्र बोर्डका अध्यक्ष सन्तोष नारायण श्रेष्ठले दिए राजीनामा",
    "image_url": "https://corporatesamachar.com/wp-content/uploads/2026/04/Santosh-Narayan-Shrestha-1732539202-300x158-1.jpg",
    "source": "Corporate Samachar",
    "article_url": "https://corporatesamachar.com/2026/04/62105/",
}


async def main():
    parser = argparse.ArgumentParser(description="NEPSE card preview generator")
    parser.add_argument("--title",    default=None,  help="Custom headline")
    parser.add_argument("--image",    default=None,  help="Custom image URL (mediaUrl)")
    parser.add_argument("--source",   default=None,  help="Source label, e.g. 'Mero Lagani'")
    parser.add_argument("--url",      default=None,  help="Article URL (launchUrl)")
    parser.add_argument("--post-id",  type=int, default=None, help="Generate from DB post ID")
    parser.add_argument("--latest",   action="store_true", help="Use latest post from DB")
    parser.add_argument("--open",     action="store_true", help="Open result in browser/Preview")
    parser.add_argument("--out",      default="preview_card.jpg", help="Output file path")
    args = parser.parse_args()

    out_path = Path(args.out)

    print("🎨 Generating news card …\n")

    if args.post_id:
        card = await from_db(args.post_id)
    elif args.latest:
        card = await from_latest_db()
        if card is None:
            print("ℹ️  No posts in database yet. Scrape first or use --title / --url flags.")
            sys.exit(0)
    elif args.title or args.url:
        card = await from_sample(
            title=args.title or SAMPLE["title"],
            image_url=args.image or SAMPLE["image_url"],
            source=args.source or SAMPLE["source"],
            article_url=args.url or SAMPLE["article_url"],
        )
    else:
        print("ℹ️  No flags given — using built-in sample article.\n")
        card = await from_sample(**SAMPLE)

    out_path.write_bytes(card)
    size_kb = len(card) // 1024
    print(f"\n✅ Card saved: {out_path.resolve()}  ({size_kb} KB)")

    if args.open:
        subprocess.run(["open", str(out_path)])  # macOS
        print("📂 Opened in Preview")


if __name__ == "__main__":
    asyncio.run(main())
