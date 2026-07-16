from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---- 创建题目 ----
class QuestionCreate(BaseModel):
    content: str = Field(..., min_length=1, description="题干文本")
    answer: str | None = Field(None, description="答案文本")
    note: str | None = Field(None, description="备注")
    source: str = Field("private", description="来源：private/public")
    system_tag_ids: list[int] = Field(default_factory=list, description="系统标签ID列表")
    user_tag_ids: list[int] = Field(default_factory=list, description="自定义标签ID列表")
    user_tag_names: list[str] = Field(default_factory=list, description="新建自定义标签名称列表")


# ---- 更新题目 ----
class QuestionUpdate(BaseModel):
    content: str | None = Field(None, description="题干文本")
    answer: str | None = Field(None, description="答案文本")
    note: str | None = Field(None, description="备注")
    system_tag_ids: list[int] | None = Field(None, description="系统标签ID列表")
    user_tag_ids: list[int] | None = Field(None, description="自定义标签ID列表")
    user_tag_names: list[str] | None = Field(None, description="新建自定义标签名称列表")


# ---- 题目响应 ----
class TagInfo(BaseModel):
    id: int
    name: str
    type: str  # "system" | "user"

    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    id: int
    user_id: int
    image_url: str | None
    content: str
    answer: str | None
    note: str | None
    source: str
    tags: list[TagInfo] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class QuestionListItem(BaseModel):
    """列表项——不暴露答案"""
    id: int
    image_url: str | None
    content: str
    source: str
    tags: list[TagInfo] = Field(default_factory=list)
    created_at: datetime | None = None

    class Config:
        from_attributes = True


# ---- OCR ----
class OCRRequest(BaseModel):
    image_url: str = Field(..., description="图片路径或base64")


class OCRResponse(BaseModel):
    content: str = ""   # 识别出的题干
    answer: str = ""     # 识别出的答案
    raw_text: str = ""   # 原始识别全文
