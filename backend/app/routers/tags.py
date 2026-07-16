"""标签管理 API 路由"""
from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.models.tag import SystemTag, UserTag
from app.models.question_tag import QuestionTag
from app.utils.response import success

router = APIRouter(prefix="/api/tags", tags=["标签"])


# ---- 请求模型 ----
class CreateUserTagRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


# ---- 响应 ----
class TagNode(BaseModel):
    id: int
    name: str
    parentId: int | None = Field(serialization_alias="parentId")
    level: int
    children: list["TagNode"] = []
    order: int = Field(serialization_alias="order")

    class Config:
        from_attributes = True
        populate_by_name = True


class UserTagResponse(BaseModel):
    id: int
    userId: int | None = Field(default=None, serialization_alias="userId")
    name: str
    questionCount: int = Field(default=0, serialization_alias="questionCount")
    createdAt: str = Field(serialization_alias="createdAt")

    class Config:
        from_attributes = True
        populate_by_name = True


# ---- 构建标签树 ----
def build_tag_tree(tags: list[SystemTag]) -> list[dict]:
    """将平铺标签转为树形结构"""
    node_map: dict[int, dict] = {}
    roots: list[dict] = []

    for t in tags:
        node = {
            "id": t.id,
            "name": t.name,
            "parentId": t.parent_id,
            "level": t.level,
            "children": [],
            "order": t.sort_order,
        }
        node_map[t.id] = node

    for node in node_map.values():
        pid = node["parentId"]
        if pid and pid in node_map:
            node_map[pid]["children"].append(node)
        else:
            roots.append(node)

    # 按 sort_order 排序
    for node in node_map.values():
        node["children"].sort(key=lambda x: (x["order"], x["id"]))
    roots.sort(key=lambda x: (x["order"], x["id"]))

    return roots


@router.get("/system")
async def api_get_system_tags(db: AsyncSession = Depends(get_db)):
    """获取系统标签树"""
    result = await db.execute(
        select(SystemTag).order_by(SystemTag.sort_order, SystemTag.id)
    )
    tags = result.scalars().all()
    tree = build_tag_tree(tags)
    return success(data=tree)


@router.get("/user")
async def api_get_user_tags(db: AsyncSession = Depends(get_db)):
    """获取用户自定义标签列表"""
    user_id = settings.DEFAULT_USER_ID
    result = await db.execute(
        select(UserTag).where(UserTag.user_id == user_id).order_by(UserTag.created_at.desc())
    )
    tags = result.scalars().all()

    items = []
    for t in tags:
        # 统计关联题目数
        count_result = await db.execute(
            select(func.count()).select_from(QuestionTag).where(
                QuestionTag.user_tag_id == t.id
            )
        )
        count = count_result.scalar()
        items.append({
            "id": t.id,
            "userId": t.user_id,
            "name": t.name,
            "questionCount": count,
            "createdAt": t.created_at.isoformat() if t.created_at else "",
        })

    return success(data=items)


@router.post("/user")
async def api_create_user_tag(
    data: CreateUserTagRequest = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """创建用户自定义标签"""
    user_id = settings.DEFAULT_USER_ID

    # 检查是否重名
    existing = await db.execute(
        select(UserTag).where(
            UserTag.user_id == user_id,
            UserTag.name == data.name.strip(),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="标签名已存在")

    tag = UserTag(user_id=user_id, name=data.name.strip())
    db.add(tag)
    await db.flush()
    await db.refresh(tag)

    return success(data={
        "id": tag.id,
        "userId": tag.user_id,
        "name": tag.name,
        "questionCount": 0,
        "createdAt": tag.created_at.isoformat() if tag.created_at else "",
    }, message="标签创建成功")


@router.delete("/user/{tag_id}")
async def api_delete_user_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除用户自定义标签"""
    tag = await db.get(UserTag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    # 删除关联
    from sqlalchemy import delete
    await db.execute(
        delete(QuestionTag).where(QuestionTag.user_tag_id == tag_id)
    )
    await db.delete(tag)
    await db.flush()

    return success(message="标签已删除")
