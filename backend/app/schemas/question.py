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
    note: str | None = Field(None, description="备注", serialization_alias="remark")
    system_tag_ids: list[int] | None = Field(None, description="系统标签ID列表", serialization_alias="systemTagIds")
    user_tag_ids: list[int] | None = Field(None, description="自定义标签ID列表", serialization_alias="userTagIds")
    user_tag_names: list[str] | None = Field(None, description="新建自定义标签名称列表", serialization_alias="userTagNames")

    class Config:
        populate_by_name = True


# ---- 题目响应 ----
class TagInfo(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    id: int
    userId: int = Field(serialization_alias="userId")
    imageUrl: str | None = Field(default=None, serialization_alias="imageUrl")
    content: str
    answer: str | None = None
    remark: str | None = Field(default=None, serialization_alias="remark")
    source: str
    systemTags: list[TagInfo] = Field(default_factory=list, serialization_alias="systemTags")
    userTags: list[TagInfo] = Field(default_factory=list, serialization_alias="userTags")
    createdAt: datetime | None = Field(default=None, serialization_alias="createdAt")
    updatedAt: datetime | None = Field(default=None, serialization_alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class QuestionListItem(BaseModel):
    """列表项——不暴露答案"""
    id: int
    imageUrl: str | None = Field(default=None, serialization_alias="imageUrl")
    content: str
    source: str
    systemTags: list[TagInfo] = Field(default_factory=list, serialization_alias="systemTags")
    userTags: list[TagInfo] = Field(default_factory=list, serialization_alias="userTags")
    createdAt: datetime | None = Field(default=None, serialization_alias="createdAt")

    class Config:
        from_attributes = True
        populate_by_name = True


# ---- OCR ----
class OCRRequest(BaseModel):
    image_url: str = Field(..., description="图片路径或base64")


class OCRResponse(BaseModel):
    content: str = ""   # 识别出的题干
    answer: str = ""     # 识别出的答案
    raw_text: str = ""   # 原始识别全文
