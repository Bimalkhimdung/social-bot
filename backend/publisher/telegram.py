"""
Telegram bot notification logic.
Handles sending approval messages and updating them, 
as well as managing the webhook.
"""

import logging
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from models.settings import Setting

logger = logging.getLogger("nepsebot.telegram")
settings = get_settings()

API_URL = "https://api.telegram.org/bot{token}"


class TelegramBot:
    async def _reload_config(self, db: AsyncSession):
        """Fetch config from DB with fallback to env."""
        keys = [
            "telegram_enabled",
            "telegram_bot_token",
            "telegram_chat_id",
            "telegram_webhook_url"
        ]
        result = await db.execute(select(Setting).where(Setting.key.in_(keys)))
        db_items = {s.key: s.value for s in result.scalars().all()}
        cfg = get_settings()

        # Handle booleans stored as strings
        enabled_val = db_items.get("telegram_enabled")
        if enabled_val is not None:
            self._enabled = enabled_val.lower() == "true"
        else:
            self._enabled = cfg.telegram_enabled

        self._token = db_items.get("telegram_bot_token") or cfg.telegram_bot_token
        self._chat_id = db_items.get("telegram_chat_id") or cfg.telegram_chat_id
        self._webhook_url = db_items.get("telegram_webhook_url") or cfg.telegram_webhook_url

    @property
    def is_enabled(self) -> bool:
        return getattr(self, "_enabled", False)

    @property
    def has_token(self) -> bool:
        return bool(getattr(self, "_token", None))

    async def set_webhook(self, db: AsyncSession):
        """Register the webhook with Telegram."""
        await self._reload_config(db)
        if not self._enabled or not self._token or not self._webhook_url:
            return
            
        url = f"{API_URL.format(token=self._token)}/setWebhook"
        webhook_target = f"{self._webhook_url.rstrip('/')}/api/telegram/webhook"
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json={"url": webhook_target})
                data = resp.json()
                if data.get("ok"):
                    logger.info(f"Telegram webhook set to {webhook_target}")
                else:
                    logger.error(f"Failed to set Telegram webhook: {data}")
        except Exception as exc:
            logger.error(f"Error setting Telegram webhook: {exc}")

    async def send_approval_request(
        self, 
        db: AsyncSession, 
        post_id: int, 
        title: str, 
        source_name: str, 
        article_url: str, 
        summary: str | None = None
    ) -> bool:
        """Send a new post notification to the admin chat with Approve/Reject inline keyboard."""
        await self._reload_config(db)
        if not self._enabled or not self._token or not self._chat_id:
            return False
            
        url = f"{API_URL.format(token=self._token)}/sendMessage"
        
        text = (
            f"🚨 <b>New Article Scraped</b>\n\n"
            f"<b>Title:</b> {title}\n"
            f"<b>Source:</b> {source_name}\n"
        )
        if summary:
            text += f"<b>Summary:</b> {summary[:200]}...\n"
        text += f"\n<a href='{article_url}'>Read Original</a>\n\nDo you want to post this to Facebook?"

        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Approve & Post", "callback_data": f"approve_{post_id}"},
                    {"text": "❌ Reject", "callback_data": f"reject_{post_id}"}
                ]
            ]
        }
        
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": keyboard,
            "disable_web_page_preview": True
        }
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                logger.info(f"Sent Telegram approval request for post_id={post_id}")
                return True
        except Exception as exc:
            logger.error(f"Failed to send Telegram approval: {exc}")
            return False

    async def edit_message_status(self, db: AsyncSession, message_id: int, post_id: int, status: str):
        """Edit the original Telegram message to remove buttons and show the outcome."""
        await self._reload_config(db)
        if not self._enabled or not self._token or not self._chat_id:
            return
            
        url = f"{API_URL.format(token=self._token)}/editMessageText"
        prefix = "✅ <b>APPROVED</b>" if status == "approved" else "❌ <b>REJECTED</b>"
        text = f"{prefix}\nPost ID: {post_id} has been {status}."
        
        payload = {
            "chat_id": self._chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, json=payload)
        except Exception as exc:
            logger.error(f"Failed to edit Telegram message: {exc}")

    async def answer_callback_query(self, db: AsyncSession, callback_query_id: str, text: str):
        """Acknowledge the callback query to stop the loading spinner in the Telegram client."""
        await self._reload_config(db)
        if not self._token:
            return
            
        url = f"{API_URL.format(token=self._token)}/answerCallbackQuery"
        payload = {
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": False
        }
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, json=payload)
        except Exception as exc:
            logger.warning(f"Failed to answer callback query: {exc}")


# Singleton
telegram_bot = TelegramBot()
