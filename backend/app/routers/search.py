"""全文检索 API 路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.search import search_questions
from app.utils.response import success, paginated

router = APIRouter(prefix="/api/search", tags=["检索"])


@router.get("")
async def api_search(
    keyword: str = Query("", description="检索关键词"),
    search_scope: str = Query("content_answer", description="检索范围：content / content_answer"),
    search_range: str = Query("all", description="来源范围：private / all"),
    system_tag_ids: str | None = Query(None, description="系统标签ID，逗号分隔"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """全文检索题目 — 支持按关键词、来源范围、标签组合筛选"""
    # 解析标签ID
    tag_ids: list[int] | None = None
    if system_tag_ids:
        tag_ids = [int(x.strip()) for x in system_tag_ids.split(",") if x.strip()]

    items, total = await search_questions(
        db,
        keyword=keyword,
        page=page,
        page_size=page_size,
        search_scope=search_scope,
        search_range=search_range,
        system_tag_ids=tag_ids,
    )

    return paginated(
        data=[item.model_dump() for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
