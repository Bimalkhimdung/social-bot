"""
Facebook / Meta Graph API publisher.

Posts to a Facebook Page using a long-lived Page Access Token.
Card generation flow:
  1. generate_news_card() → JPEG bytes
  2. upload_photo()       → FB photo_id
  3. publish()            → FB post_id (with attached photo)

Runs in dry-run mode when FB_PAGE_ACCESS_TOKEN or FB_PAGE_ID are not set.
Retry logic: exponential backoff (1s, 2s, 4s) on transient errors.
"""

import logging
import time
from datetime import datetime, date

import httpx

from config import get_settings

logger = logging.getLogger("nepsebot.publisher")
settings = get_settings()

FB_GRAPH_BASE = "https://graph.facebook.com/v19.0"


# ---------------------------------------------------------------------------
# Caption builder
# ---------------------------------------------------------------------------

def build_caption(title: str, source_name: str, article_url: str, keywords: list[str]) -> str:
    """Render the caption template with article metadata."""
    template = settings.caption_template
    hashtags = settings.default_hashtags

    extra = " ".join(f"#{kw.replace(' ', '')}" for kw in keywords[:5] if kw.isascii())
    if extra:
        hashtags = f"{hashtags} {extra}"

    caption = template.format(
        title=title,
        source=source_name,
        date=date.today().strftime("%Y-%m-%d"),
        hashtags=hashtags,
        url=article_url,
    )
    return caption


# ---------------------------------------------------------------------------
# Publisher
# ---------------------------------------------------------------------------

class FacebookPublisher:
    def __init__(self):
        self._token = settings.fb_page_access_token
        self._page_id = settings.fb_page_id

    @property
    def is_configured(self) -> bool:
        return bool(self._token and self._page_id)

    def _reload_config(self):
        cfg = get_settings()
        self._token = cfg.fb_page_access_token
        self._page_id = cfg.fb_page_id

    async def upload_photo(self, image_bytes: bytes) -> str | None:
        """
        Upload image bytes to Facebook Page Photos (unpublished).
        Returns photo_id to attach to a post, or None on failure.
        """
        self._reload_config()
        if not self.is_configured:
            return None

        endpoint = f"{FB_GRAPH_BASE}/{self._page_id}/photos"
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    endpoint,
                    data={"access_token": self._token, "published": "false"},
                    files={"source": ("card.jpg", image_bytes, "image/jpeg")},
                )
                resp.raise_for_status()
                data = resp.json()
                photo_id = data.get("id")
                logger.info(f"Photo uploaded to Facebook: photo_id={photo_id}")
                return photo_id
        except Exception as exc:
            logger.error(f"Photo upload failed: {exc}", exc_info=True)
            return None

    def publish(
        self,
        *,
        title: str,
        article_url: str,
        caption: str,
        image_url: str | None = None,
        photo_id: str | None = None,    # ← FB photo uploaded via upload_photo()
        dry_run: bool = False,
    ) -> str | None:
        """
        Publish a post to the Facebook page.
        If photo_id is provided, attaches the pre-uploaded card image.
        Returns the fb_post_id on success, None on failure/dry-run.
        """
        self._reload_config()

        if dry_run or not self.is_configured:
            logger.info(
                f"[DRY-RUN] Would post to FB Page {self._page_id or '?'}: "
                f"{title[:60]} | card={'yes' if photo_id else 'no'} | {article_url}"
            )
            return None

        endpoint = f"{FB_GRAPH_BASE}/{self._page_id}/feed"
        payload: dict = {
            "access_token": self._token,
            "message": caption,
        }

        if photo_id:
            # Post with attached card image
            import json as _json
            payload["attached_media"] = _json.dumps([{"media_fbid": photo_id}])
        else:
            # Fallback: link post with article URL
            payload["link"] = article_url

        for attempt in range(3):
            try:
                resp = httpx.post(endpoint, data=payload, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                fb_post_id = data.get("id")
                logger.info(f"Published to Facebook: post_id={fb_post_id} | {title[:60]}")
                return fb_post_id
            except httpx.HTTPStatusError as exc:
                error_body = exc.response.text
                logger.error(
                    f"FB API error (attempt {attempt + 1}/3): "
                    f"{exc.response.status_code} — {error_body}"
                )
                if exc.response.status_code in (400, 401, 403):
                    break
                wait = 2 ** attempt
                logger.info(f"Retrying in {wait}s…")
                time.sleep(wait)
            except Exception as exc:
                logger.error(f"Facebook publish error (attempt {attempt + 1}/3): {exc}", exc_info=True)
                wait = 2 ** attempt
                time.sleep(wait)

        return None


# Singleton
publisher = FacebookPublisher()
