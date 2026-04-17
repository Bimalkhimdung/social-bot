import json
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (
        Index("ix_articles_url_hash", "url_hash", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_label: Mapped[str | None] = mapped_column(String(200), nullable=True)  # e.g. "Corporate Samachar"
    article_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    keywords: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    source: Mapped["Source"] = relationship("Source", back_populates="articles", lazy="select")
    post: Mapped["Post | None"] = relationship("Post", back_populates="article", uselist=False, lazy="select")

    @property
    def keywords_list(self) -> list[str]:
        try:
            return json.loads(self.keywords)
        except Exception:
            return []
