from datetime import UTC, datetime

from app.domain.aggregates.comment import Comment
from app.domain.value_objects.message_text import MessageText
from app.domain.value_objects.username import Username
from app.infrastructure.db.models import CommentModel


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class CommentMapper:
    """маппер между orm-моделью и доменным комментарием"""

    @staticmethod
    def to_domain(model: CommentModel) -> Comment:
        created_at = _as_utc(model.created_at)
        if created_at is None:
            raise ValueError("CommentModel created_at must not be None")
        ext_id: int | str | None = None
        if model.external_id is not None:
            if isinstance(model.external_id, int):
                ext_id = model.external_id
            elif isinstance(model.external_id, str):
                ext_id = (
                    int(model.external_id)
                    if model.external_id.isdigit()
                    else model.external_id
                )
            else:
                ext_id = str(model.external_id)
        return Comment(
            id=model.id,
            source_url=model.source_url,
            external_id=ext_id,
            author=Username.from_str(model.author),
            text=MessageText.from_str(model.text),
            created_at=created_at,
            updated_at=_as_utc(model.updated_at),
            version=model.version,
        )

    @staticmethod
    def to_model(entity: Comment) -> CommentModel:
        return CommentModel(
            id=entity.id,
            source_url=entity.source_url,
            external_id=(
                str(entity.external_id)
                if entity.external_id is not None
                else None
            ),
            author=entity.author.value,
            text=entity.text.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            version=entity.version,
        )
