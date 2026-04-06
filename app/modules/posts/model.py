from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    place_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("places.id"), nullable=True, index=True)

    caption: Mapped[str | None] = mapped_column(String(500), nullable=True)
    media_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    media_urls_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    hashtags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    gem_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    aura_points: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
