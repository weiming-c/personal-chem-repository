from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WrongQuestion(Base):
    """错题记录——独立管理，支持状态流转"""
    __tablename__ = "wrong_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(default=1, index=True, comment="用户ID")
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )

    # 错题动态记录
    error_count: Mapped[int] = mapped_column(Integer, default=1, comment="错误次数")
    note: Mapped[str | None] = mapped_column(Text, comment="错题笔记/错因分析")

    # 状态：active=错题中, mastered=已掌握, removed=已移除
    status: Mapped[str] = mapped_column(
        String(20), default="active",
        comment="状态：active/mastered/removed"
    )

    last_review_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="上次复习时间"
    )
    next_review_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="下次推荐复习时间（艾宾浩斯用）"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
