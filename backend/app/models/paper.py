from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Paper(Base):
    """组卷/试卷"""
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(default=1, index=True, comment="用户ID")
    title: Mapped[str] = mapped_column(String(200), comment="试卷标题")

    # 来源：private/public/mixed
    source_filter: Mapped[str | None] = mapped_column(
        String(20), comment="组卷来源筛选"
    )

    # 组卷条件（JSON 字符串，方便扩展）
    conditions: Mapped[str | None] = mapped_column(
        Text, comment="组卷条件 JSON"
    )

    question_count: Mapped[int] = mapped_column(Integer, default=0, comment="题目数量")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PaperQuestion(Base):
    """试卷-题目关联，可自定义排序"""
    __tablename__ = "paper_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("papers.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("questions.id", ondelete="CASCADE")
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
