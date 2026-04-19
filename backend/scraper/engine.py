"""
Core scraping engine.

Supports two source types:
  - "html"  → httpx GET + BeautifulSoup CSS selectors
  - "api"   → httpx GET + JSON path traversal (e.g. ShareHub Nepal)

Deduplication is handled by storing a SHA-256 hash of the article URL.
Keyword filtering only passes articles matching the configurable whitelist.
"""

import hashlib
import json
import logging
import re
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from models.article import Article
from models.post import Post, PostStatus
from models.source import Source

logger = logging.getLogger("nepsebot.scraper")
settings = get_settings()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; NEPSEBot/1.0; +https://github.com/nepsebot) "
        "AppleWebKit/537.36 (KHTML, like Gecko)"
    ),
    "Accept-Language": "en-US,en;q=0.9,ne;q=0.8",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _url_hash(url: str) -> str:
    return hashlib.sha256(url.strip().encode()).hexdigest()


def _keyword_match(text: str, keywords: list[str]) -> list[str]:
    """Return the keywords found in text (case-insensitive)."""
    text_lower = text.lower()
    return [kw for kw in keywords if kw.lower() in text_lower]


def _resolve_url(href: str, base_url: str) -> str:
    if href.startswith("http"):
        return href
    return urljoin(base_url, href)


def _get_nested(data: dict | list, dot_path: str) -> Any:
    """Traverse a dict/list using dot notation. E.g. 'data.0.imageUrl'"""
    parts = dot_path.split(".")
    for part in parts:
        if isinstance(data, dict):
            data = data.get(part)
        elif isinstance(data, list) and part.isdigit():
            idx = int(part)
            if idx < len(data):
                data = data[idx]
            else:
                return None
        else:
            return None
    return data


# ---------------------------------------------------------------------------
# Per-source scrapers
# ---------------------------------------------------------------------------

async def _scrape_html(source: Source, client: httpx.AsyncClient) -> list[dict]:
    cfg = source.selector_config_dict
    title_selector = cfg.get("title_selector", "h2 a, h3 a, h5 a")
    base_url = cfg.get("base_url", "")
    image_selector = cfg.get("image_selector", "img")
    image_attr = cfg.get("image_attr", "src")
    results = []

    try:
        resp = await client.get(source.url, headers=HEADERS, timeout=20, follow_redirects=True)
        resp.raise_for_status()
    except Exception as exc:
        logger.warning(f"[{source.name}] HTTP error: {exc}")
        return results

    soup = BeautifulSoup(resp.text, "lxml")

    seen_urls: set[str] = set()
    for tag in soup.select(title_selector):
        title = tag.get_text(strip=True)
        href = tag.get("href", "")
        if not href or not title:
            continue
        article_url = _resolve_url(href, base_url)
        if article_url in seen_urls:
            continue
        seen_urls.add(article_url)

        # Try to grab a nearby image
        image_url = None
        parent = tag.find_parent(["article", "div", "li", "section"])
        if parent:
            img = parent.select_one(image_selector)
            if img:
                image_url = img.get(image_attr) or img.get("data-src")

        # Grab a summary snippet
        summary = None
        if parent:
            p = parent.find("p")
            if p:
                summary = p.get_text(strip=True)[:400]

        results.append({
            "title": title,
            "article_url": article_url,
            "summary": summary,
            "image_url": image_url,
            "source_label": None,
        })

    return results


async def _scrape_api(source: Source, client: httpx.AsyncClient) -> list[dict]:
    cfg = source.selector_config_dict
    data_path = cfg.get("data_path", "data")
    title_field = cfg.get("title_field", "name")
    url_field = cfg.get("url_field", "url")
    url_template = cfg.get("url_template", "")
    image_field = cfg.get("image_field", "imageUrl")
    summary_field = cfg.get("summary_field", "")
    source_label_field = cfg.get("source_label_field", "")
    results = []

    try:
        # Use a more API-friendly URL with _embed for Wordpress sources when possible
        fetch_url = source.url
        if "wp-json/wp/v2/posts" in fetch_url and "_embed" not in fetch_url:
            fetch_url += "&_embed=1" if "?" in fetch_url else "?_embed=1"

        resp = await client.get(fetch_url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning(f"[{source.name}] API error: {exc}")
        return results

    # If data_path is empty, data is the root array (Wordpress standard)
    items = _get_nested(data, data_path) if data_path else data
    if not isinstance(items, list):
        logger.warning(f"[{source.name}] Unexpected API data shape — got {type(items)}")
        return results

    for item in items:
        # Evaluate nested objects dynamically
        title = _get_nested(item, title_field)
        if isinstance(title, dict) and "rendered" in title:
            title = BeautifulSoup(title["rendered"], "html.parser").get_text()
            
        raw_url = _get_nested(item, url_field) or ""
        
        if url_template and raw_url:
            article_url = url_template.replace("{" + url_field + "}", raw_url)
        else:
            article_url = raw_url

        image_url = _get_nested(item, image_field)
        
        summary = _get_nested(item, summary_field) if summary_field else None
        if isinstance(summary, dict) and "rendered" in summary:
            summary = BeautifulSoup(summary["rendered"], "html.parser").get_text(strip=True)[:400]

        source_label = _get_nested(item, source_label_field) if source_label_field else None

        if not title or not article_url:
            continue

        results.append({
            "title": title,
            "article_url": article_url,
            "summary": str(summary) if summary else None,
            "image_url": str(image_url) if image_url else None,
            "source_label": str(source_label) if source_label else None,
        })

    return results


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

async def scrape_source(source: Source, db: AsyncSession) -> dict[str, int]:
    """Scrape a single source, deduplicate, keyword-filter, and insert articles."""
    keywords = settings.keyword_filter

    async with httpx.AsyncClient() as client:
        if source.source_type == "api":
            raw_items = await _scrape_api(source, client)
        else:
            raw_items = await _scrape_html(source, client)

    new_count = 0
    skipped_dedup = 0
    skipped_kw = 0

    for item in raw_items:
        article_url = item["article_url"]
        title = item["title"]
        summary = item.get("summary") or ""
        url_hash = _url_hash(article_url)

        # Dedup check
        existing = await db.scalar(select(Article).where(Article.url_hash == url_hash))
        if existing:
            skipped_dedup += 1
            continue

        # Keyword filter — check title + summary
        combined_text = f"{title} {summary}"
        matched_kws = _keyword_match(combined_text, keywords)
        if settings.enable_keyword_filter and not matched_kws:
            skipped_kw += 1
            logger.debug(f"[{source.name}] Skipped (no keyword match): {title[:60]}")
            continue

        article = Article(
            source_id=source.id,
            title=title,
            summary=summary or None,
            image_url=item.get("image_url"),
            source_label=item.get("source_label"),
            article_url=article_url,
            url_hash=url_hash,
            keywords=json.dumps(matched_kws),
            scraped_at=datetime.utcnow(),
        )
        db.add(article)
        await db.flush()  # get article.id

        # Auto-approve logic
        auto_approve = settings.auto_approve
        status = PostStatus.approved if auto_approve else PostStatus.pending

        post = Post(
            article_id=article.id,
            status=status,
            caption=None,
        )
        db.add(post)
        new_count += 1
        logger.info(f"[{source.name}] New article: {title[:70]} | status={status.value}")

    # Update last_scraped_at
    source.last_scraped_at = datetime.utcnow()
    await db.commit()

    return {"new": new_count, "skipped_dedup": skipped_dedup, "skipped_kw": skipped_kw}


async def scrape_all_sources(db: AsyncSession) -> dict[str, Any]:
    """Scrape all active sources. Called by scheduler."""
    result = await db.execute(select(Source).where(Source.is_active == True))  # noqa: E712
    sources = result.scalars().all()

    total = {"new": 0, "skipped_dedup": 0, "skipped_kw": 0}
    for source in sources:
        logger.info(f"Scraping source: {source.name} ({source.url})")
        try:
            stats = await scrape_source(source, db)
            for k in total:
                total[k] += stats.get(k, 0)
        except Exception as exc:
            logger.error(f"Error scraping {source.name}: {exc}", exc_info=True)

    logger.info(f"Scrape complete: {total}")
    return total
