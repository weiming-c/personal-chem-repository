from datetime import datetime

from sqlalchemy import Integer, ForeignKey, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class QuestionTag(Base):
    """题目-标签关联表（同时关联系统标签和用户标签）"""
    __tablename__ = "question_tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    system_tag_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("system_tags.id", ondelete="CASCADE"), nullable=True
    )
    user_tag_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("user_tags.id", ondelete="CASCADE"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
