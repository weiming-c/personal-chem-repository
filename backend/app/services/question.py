"""题目业务服务"""
from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.config import settings
from app.models.question import Question
from app.models.tag import SystemTag, UserTag
from app.models.question_tag import QuestionTag
from app.models.wrong_question import WrongQuestion
from app.schemas.question import (
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    QuestionListItem,
    TagInfo,
)
from app.services.upload import save_upload


async def _get_tags_for_question(db: AsyncSession, question_id: int) -> tuple[list[TagInfo], list[TagInfo]]:
    """获取题目的所有标签，返回 (systemTags, userTags)"""
    system_tags: list[TagInfo] = []
    user_tags: list[TagInfo] = []

    # 系统标签
    stmt = (
        select(QuestionTag, SystemTag)
        .join(SystemTag, QuestionTag.system_tag_id == SystemTag.id)
        .where(QuestionTag.question_id == question_id)
    )
    result = await db.execute(stmt)
    for _, stag in result.all():
        system_tags.append(TagInfo(id=stag.id, name=stag.name))

    # 用户标签
    stmt = (
        select(QuestionTag, UserTag)
        .join(UserTag, QuestionTag.user_tag_id == UserTag.id)
        .where(QuestionTag.question_id == question_id)
    )
    result = await db.execute(stmt)
    for _, utag in result.all():
        user_tags.append(TagInfo(id=utag.id, name=utag.name))

    return system_tags, user_tags


async def _sync_tags(
    db: AsyncSession,
    question_id: int,
    system_tag_ids: list[int] | None,
    user_tag_ids: list[int] | None,
    user_tag_names: list[str] | None,
):
    """同步题目标签：先清再建 + 新建用户标签"""
    if system_tag_ids is None and user_tag_ids is None and user_tag_names is None:
        return  # 更新时不传标签字段，表示保持原样

    user_id = settings.DEFAULT_USER_ID

    # 处理新建自定义标签
    if user_tag_names:
        for name in user_tag_names:
            name = name.strip()
            if not name:
                continue
            # 检查是否已存在
            existing = await db.execute(
                select(UserTag).where(
                    UserTag.user_id == user_id,
                    UserTag.name == name,
                )
            )
            tag = existing.scalar_one_or_none()
            if tag is None:
                tag = UserTag(user_id=user_id, name=name)
                db.add(tag)
                await db.flush()
            # 追加到 user_tag_ids
            if user_tag_ids is None:
                user_tag_ids = []
            if tag.id not in user_tag_ids:
                user_tag_ids.append(tag.id)

    # 清除旧标签
    await db.execute(
        delete(QuestionTag).where(QuestionTag.question_id == question_id)
    )

    # 插入新标签
    if system_tag_ids:
        for sid in system_tag_ids:
            db.add(QuestionTag(question_id=question_id, system_tag_id=sid))
    if user_tag_ids:
        for uid in user_tag_ids:
            db.add(QuestionTag(question_id=question_id, user_tag_id=uid))

    await db.flush()


async def create_question(
    db: AsyncSession,
    data: QuestionCreate,
    image_url: str | None = None,
    image: UploadFile | None = None,
    answer_image_url: str | None = None,
) -> QuestionResponse:
    """创建题目"""
    user_id = settings.DEFAULT_USER_ID

    # 处理题图：优先用已上传的URL，其次处理直接上传的文件
    final_image_url = image_url or None
    if final_image_url is None and image and image.filename:
        final_image_url = await save_upload(image)

    question = Question(
        user_id=user_id,
        content=data.content,
        answer=data.answer,
        note=data.note,
        source=data.source,
        image_url=final_image_url,
        answer_image_url=answer_image_url or None,
    )
    db.add(question)
    await db.flush()  # 获取 question.id

    # 处理标签
    await _sync_tags(
        db,
        question.id,
        data.system_tag_ids,
        data.user_tag_ids,
        data.user_tag_names,
    )

    await db.refresh(question)
    system_tags, user_tags = await _get_tags_for_question(db, question.id)
    return QuestionResponse(
        id=question.id,
        userId=question.user_id,
        imageUrl=question.image_url,
        answerImageUrl=question.answer_image_url,
        content=question.content,
        answer=question.answer,
        remark=question.note,
        source=question.source,
        systemTags=system_tags,
        userTags=user_tags,
        createdAt=question.created_at,
        updatedAt=question.updated_at,
    )


async def get_question(db: AsyncSession, question_id: int) -> QuestionResponse:
    """获取题目详情"""
    question = await db.get(Question, question_id)
    if not question or question.is_deleted:
        raise HTTPException(status_code=404, detail="题目不存在")

    system_tags, user_tags = await _get_tags_for_question(db, question_id)
    return QuestionResponse(
        id=question.id,
        userId=question.user_id,
        imageUrl=question.image_url,
        answerImageUrl=question.answer_image_url,
        content=question.content,
        answer=question.answer,
        remark=question.note,
        source=question.source,
        systemTags=system_tags,
        userTags=user_tags,
        createdAt=question.created_at,
        updatedAt=question.updated_at,
    )


async def list_questions(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    source: str | None = None,
    system_tag_id: int | None = None,
    user_tag_id: int | None = None,
    keyword: str | None = None,
) -> tuple[list[QuestionListItem], int]:
    """分页查询题目列表"""
    user_id = settings.DEFAULT_USER_ID

    # 基础条件
    conditions = [
        Question.user_id == user_id,
        Question.is_deleted == False,
    ]
    if source:
        conditions.append(Question.source == source)

    # 标签筛选
    if system_tag_id:
        conditions.append(
            Question.id.in_(
                select(QuestionTag.question_id).where(
                    QuestionTag.system_tag_id == system_tag_id
                )
            )
        )
    if user_tag_id:
        conditions.append(
            Question.id.in_(
                select(QuestionTag.question_id).where(
                    QuestionTag.user_tag_id == user_tag_id
                )
            )
        )

    # 关键词搜索（ILIKE 简易全文检索）
    if keyword:
        like_pattern = f"%{keyword}%"
        conditions.append(
            (Question.content.ilike(like_pattern)) |
            (Question.answer.ilike(like_pattern))
        )

    # 计数
    count_stmt = select(func.count()).select_from(Question).where(*conditions)
    total = (await db.execute(count_stmt)).scalar_one()

    # 分页查询
    stmt = (
        select(Question)
        .where(*conditions)
        .order_by(Question.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    questions = result.scalars().all()

    items = []
    for q in questions:
        system_tags, user_tags = await _get_tags_for_question(db, q.id)
        items.append(QuestionListItem(
            id=q.id,
            imageUrl=q.image_url,
            answerImageUrl=q.answer_image_url,
            content=q.content,
            source=q.source,
            systemTags=system_tags,
            userTags=user_tags,
            createdAt=q.created_at,
        ))

    return items, total


async def update_question(
    db: AsyncSession,
    question_id: int,
    data: QuestionUpdate,
) -> QuestionResponse:
    """更新题目"""
    question = await db.get(Question, question_id)
    if not question or question.is_deleted:
        raise HTTPException(status_code=404, detail="题目不存在")

    if data.content is not None:
        question.content = data.content
    if data.answer is not None:
        question.answer = data.answer
    if data.note is not None:
        question.note = data.note
    if data.image_url is not None:
        question.image_url = data.image_url
    if data.answer_image_url is not None:
        question.answer_image_url = data.answer_image_url

    # 同步标签（传了标签字段才更新）
    if data.system_tag_ids is not None or data.user_tag_ids is not None or data.user_tag_names is not None:
        await _sync_tags(
            db,
            question_id,
            data.system_tag_ids,
            data.user_tag_ids,
            data.user_tag_names,
        )

    await db.flush()
    await db.refresh(question)

    system_tags, user_tags = await _get_tags_for_question(db, question_id)
    return QuestionResponse(
        id=question.id,
        userId=question.user_id,
        imageUrl=question.image_url,
        answerImageUrl=question.answer_image_url,
        content=question.content,
        answer=question.answer,
        remark=question.note,
        source=question.source,
        systemTags=system_tags,
        userTags=user_tags,
        createdAt=question.created_at,
        updatedAt=question.updated_at,
    )


async def delete_question(db: AsyncSession, question_id: int):
    """软删除题目"""
    question = await db.get(Question, question_id)
    if not question or question.is_deleted:
        raise HTTPException(status_code=404, detail="题目不存在")

    question.is_deleted = True
    await db.flush()
