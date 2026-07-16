from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.database import Base


class SystemTag(Base):
    """系统预设标签——树形化学知识点体系"""
    __tablename__ = "system_tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), comment="标签名称")
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("system_tags.id"), nullable=True, comment="父级标签ID"
    )
    level: Mapped[int] = mapped_column(Integer, default=1, comment="层级：1=模块 2=章节 3=知识点")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserTag(Base):
    """用户自定义标签——扁平私有标签"""
    __tablename__ = "user_tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(default=1, index=True, comment="用户ID")
    name: Mapped[str] = mapped_column(String(100), comment="标签名称")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
