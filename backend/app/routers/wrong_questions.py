"""错题本 API 路由"""
from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.wrong_question import (
    list_wrong_questions,
    mark_wrong,
    update_wrong_question,
    remove_wrong_question,
)
from app.utils.response import success, paginated

router = APIRouter(prefix="/api/wrong-questions", tags=["错题"])


class MarkWrongRequest(BaseModel):
    questionId: int = Field(..., serialization_alias="questionId")

    class Config:
        populate_by_name = True


class UpdateWrongRequest(BaseModel):
    status: str | None = None
    note: str | None = None
    wrongReason: str | None = Field(None, serialization_alias="wrongReason")

    class Config:
        populate_by_name = True


@router.get("")
async def api_list_wrong_questions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    system_tag_ids: str | None = Query(None, alias="systemTagIds"),
    wrong_count_min: int | None = Query(None, alias="wrongCountMin"),
    wrong_count_max: int | None = Query(None, alias="wrongCountMax"),
    db: AsyncSession = Depends(get_db),
):
    """分页查询错题列表"""
    tag_ids: list[int] | None = None
    if system_tag_ids:
        tag_ids = [int(x.strip()) for x in system_tag_ids.split(",") if x.strip()]

    items, total = await list_wrong_questions(
        db,
        page=page,
        page_size=page_size,
        status=status,
        system_tag_ids=tag_ids,
        wrong_count_min=wrong_count_min,
        wrong_count_max=wrong_count_max,
    )

    return paginated(data=items, total=total, page=page, page_size=page_size)


@router.post("")
async def api_mark_wrong(
    data: MarkWrongRequest = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """标记题目为错题"""
    result = await mark_wrong(db, data.questionId)
    return success(data=result, message="已加入错题本")


@router.put("/{wq_id}")
async def api_update_wrong(
    wq_id: int,
    data: UpdateWrongRequest = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """更新错题记录"""
    result = await update_wrong_question(
        db,
        wq_id,
        status=data.status,
        note=data.note,
        wrong_reason=data.wrongReason,
    )
    return success(data=result, message="已更新")


@router.delete("/{wq_id}")
async def api_delete_wrong(
    wq_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除错题记录"""
    await remove_wrong_question(db, wq_id)
    return success(message="已移除")
