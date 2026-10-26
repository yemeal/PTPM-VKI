import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class CommentModel(Base):
    """orm-модель таблицы комментариев"""

    __tablename__ = "comments"
    __table_args__ = (
        Index(
            "uq_comments_source_external_id",
            "source_url",
            "external_id",
            unique=True,
            sqlite_where=text("external_id IS NOT NULL"),
            postgresql_where=text("external_id IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_url: Mapped[str] = mapped_column(
        String(2048), nullable=False, index=True
    )
    external_id: Mapped[str | None] = mapped_column(
        String(256), nullable=True, default=None
    )
    author: Mapped[str] = mapped_column(
        String(256), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
