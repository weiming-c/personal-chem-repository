"""错题本业务服务"""
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.wrong_question import WrongQuestion
from app.models.question import Question
from app.models.question_tag import QuestionTag


async def _build_wq_response(db: AsyncSession, wq: WrongQuestion) -> dict:
    """构建错题响应（含题目预览）"""
    question = await db.get(Question, wq.question_id)
    return {
        "id": wq.id,
        "userId": wq.user_id,
        "questionId": wq.question_id,
        "question": {
            "id": question.id,
            "imageUrl": question.image_url,
            "answerImageUrl": question.answer_image_url,
            "content": (question.content[:100] + "..." if question.content and len(question.content) > 100 else question.content) if question else "",
            "source": question.source if question else "private",
            "systemTags": [],
            "userTags": [],
            "createdAt": question.created_at.isoformat() if question and question.created_at else None,
        } if question else None,
        "wrongCount": wq.error_count,
        "status": wq.status,
        "note": wq.note or "",
        "wrongReason": "",
        "lastWrongAt": wq.updated_at.isoformat() if wq.updated_at else "",
        "nextReviewAt": wq.next_review_at.isoformat() if wq.next_review_at else None,
        "createdAt": wq.created_at.isoformat() if wq.created_at else "",
        "updatedAt": wq.updated_at.isoformat() if wq.updated_at else "",
    }


async def list_wrong_questions(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    system_tag_ids: list[int] | None = None,
    wrong_count_min: int | None = None,
    wrong_count_max: int | None = None,
) -> tuple[list[dict], int]:
    """分页查询错题列表"""
    user_id = settings.DEFAULT_USER_ID
    conditions = [WrongQuestion.user_id == user_id]

    if status:
        conditions.append(WrongQuestion.status == status)
    if wrong_count_min is not None:
        conditions.append(WrongQuestion.error_count >= wrong_count_min)
    if wrong_count_max is not None:
        conditions.append(WrongQuestion.error_count <= wrong_count_max)

    # 标签筛选
    if system_tag_ids:
        conditions.append(
            WrongQuestion.question_id.in_(
                select(QuestionTag.question_id).where(
                    QuestionTag.system_tag_id.in_(system_tag_ids)
                )
            )
        )

    count_stmt = select(func.count()).select_from(WrongQuestion).where(*conditions)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(WrongQuestion)
        .where(*conditions)
        .order_by(WrongQuestion.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    wqs = result.scalars().all()

    items = []
    for wq in wqs:
        items.append(await _build_wq_response(db, wq))

    return items, total


async def mark_wrong(db: AsyncSession, question_id: int) -> dict:
    """标记为错题（若已存在则错误次数+1）"""
    user_id = settings.DEFAULT_USER_ID

    # 检查题目是否存在
    question = await db.get(Question, question_id)
    if not question or question.is_deleted:
        raise HTTPException(status_code=404, detail="题目不存在")

    # 查找已有错题记录
    result = await db.execute(
        select(WrongQuestion).where(
            WrongQuestion.user_id == user_id,
            WrongQuestion.question_id == question_id,
        )
    )
    existing = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if existing:
        existing.error_count += 1
        existing.status = "active"
        existing.updated_at = now
        existing.last_review_at = now
        await db.flush()
        await db.refresh(existing)
        return await _build_wq_response(db, existing)
    else:
        wq = WrongQuestion(
            user_id=user_id,
            question_id=question_id,
            error_count=1,
            status="active",
            last_review_at=now,
        )
        db.add(wq)
        await db.flush()
        await db.refresh(wq)
        return await _build_wq_response(db, wq)


async def update_wrong_question(
    db: AsyncSession,
    wq_id: int,
    status: str | None = None,
    note: str | None = None,
    wrong_reason: str | None = None,
) -> dict:
    """更新错题状态/笔记"""
    wq = await db.get(WrongQuestion, wq_id)
    if not wq:
        raise HTTPException(status_code=404, detail="错题记录不存在")

    now = datetime.now(timezone.utc)
    if status is not None:
        wq.status = status
    if note is not None:
        wq.note = note
    if wrong_reason is not None:
        # wrongReason 存储在 note 字段中，用前缀区分
        # 简单策略：如果 wrongReason 非空则存到 note
        if note is None:
            wq.note = wrong_reason
    wq.updated_at = now

    if status == "mastered":
        wq.last_review_at = now

    await db.flush()
    await db.refresh(wq)
    return await _build_wq_response(db, wq)


async def remove_wrong_question(db: AsyncSession, wq_id: int):
    """删除错题记录（真删除）"""
    wq = await db.get(WrongQuestion, wq_id)
    if not wq:
        raise HTTPException(status_code=404, detail="错题记录不存在")
    await db.delete(wq)
    await db.flush()
