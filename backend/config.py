from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://bimalrai:bimalrai@localhost:5432/nepsebot"

    # Auth
    admin_password: str = "changeme123"
    jwt_secret: str = "supersecretjwtsecret"
    jwt_expire_minutes: int = 1440

    # Facebook
    fb_page_access_token: str = ""
    fb_page_id: str = ""

    # Telegram
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_webhook_url: str = ""

    # Scheduler
    scrape_interval_minutes: int = 30
    publish_interval_minutes: int = 30
    max_posts_per_day: int = 4
    quiet_hours_start: int = 22
    quiet_hours_end: int = 6
    auto_approve: bool = False
    auto_publish: bool = True


    # Caption
    caption_template: str = "📰 {title}\n\n🔗 {source} | {date}\n\n{hashtags}"
    default_hashtags: str = "#NEPSE #ShareMarket #Nepal #StockMarket #लगानी #सेयर"

    # CORS
    frontend_url: str = "http://localhost:5173"

    # Logging
    log_level: str = "INFO"

    # Keywords
    enable_keyword_filter: bool = True
    # Keyword filter (comma-separated in .env, or use this default list)
    keyword_filter: list[str] = [
        "NEPSE", "share market", "stock market", "IPO", "FPO", "right share",
        "bonus share", "dividend", "SEBON", "broker", "demat", "Meroshare",
        "circuit breaker", "bullish", "bearish", "NEPSE index",
        "लगानी", "सेयर", "बजार", "शेयर", "नेप्से", "ब्रोकर", 
        "नेपाल राष्ट्र बैंक", "सर्किट ब्रेकर", "सेयर बजार", "लाभांश", "हकप्रद"
    ]



@lru_cache
def get_settings() -> Settings:
    return Settings()
