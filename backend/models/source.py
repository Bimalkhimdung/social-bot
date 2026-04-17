import enum
import json
from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="html")  # "html" | "api"
    selector_config: Mapped[str] = mapped_column(Text, default="{}")  # JSON string
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_scraped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    articles: Mapped[list["Article"]] = relationship("Article", back_populates="source", lazy="select")

    @property
    def selector_config_dict(self) -> dict:
        try:
            return json.loads(self.selector_config)
        except Exception:
            return {}
