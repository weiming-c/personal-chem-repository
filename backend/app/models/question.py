from datetime import datetime

from sqlalchemy import String, Text, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(default=1, index=True,
                                          comment="预留多用户扩展位，MVP 默认为 1")

    # 题目内容
    image_url: Mapped[str | None] = mapped_column(String(500), comment="题图存储路径（增强后）")
    raw_image_url: Mapped[str | None] = mapped_column(String(500), comment="题图原图备份路径")
    answer_image_url: Mapped[str | None] = mapped_column(String(500), comment="答案图存储路径")
    content: Mapped[str] = mapped_column(Text, comment="题干文本")
    answer: Mapped[str | None] = mapped_column(Text, comment="答案文本")
    note: Mapped[str | None] = mapped_column(Text, comment="用户备注")

    # 来源标识：private / public
    source: Mapped[str] = mapped_column(
        String(20), default="private",
        comment="题目来源：private=私有, public=公共"
    )

    # 是否启用 PostgreSQL 全文检索向量
    search_vector: Mapped[str | None] = mapped_column(Text, comment="pg_bigm 搜索用")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="软删除标记"
    )
