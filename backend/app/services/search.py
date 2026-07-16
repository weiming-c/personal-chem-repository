"""全文检索服务 — tsvector + ILIKE 双模检索，兼容中英文"""
from sqlalchemy import select, func, text, or_, and_, literal_column
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.question import Question
from app.models.question_tag import QuestionTag
from app.schemas.question import QuestionListItem, TagInfo
from app.services.question import _get_tags_for_question


def _make_keyword_cond(keyword: str, search_scope: str):
    """构建关键词搜索条件，tsvector 与 ILIKE 并用覆盖中英文"""
    keyword = keyword.strip()
    if not keyword:
        return None

    like_pattern = f"%{keyword}%"

    if search_scope == "content":
        ilike_cond = Question.content.ilike(like_pattern)
    else:
        ilike_cond = or_(
            Question.content.ilike(like_pattern),
            Question.answer.ilike(like_pattern),
        )

    # tsvector 检索（英文/数字/化学式等）
    tsquery = func.plainto_tsquery(text("'simple'"), keyword)
    if search_scope == "content":
        ts_cond = literal_column("content_tsv").op("@@")(tsquery)
    else:
        ts_cond = or_(
            literal_column("content_tsv").op("@@")(tsquery),
            literal_column("answer_tsv").op("@@")(tsquery),
        )

    # ILIKE 或 tsvector 满足其一即可
    return or_(ilike_cond, ts_cond)


async def search_questions(
    db: AsyncSession,
    keyword: str,
    page: int = 1,
    page_size: int = 20,
    search_scope: str = "content_answer",
    search_range: str = "all",
    system_tag_ids: list[int] | None = None,
) -> tuple[list[QuestionListItem], int]:
    """全文检索题目 — tsvector + ILIKE 双模，兼容中英文搜索"""
    user_id = settings.DEFAULT_USER_ID

    # 基础条件
    conditions = [
        Question.user_id == user_id,
        Question.is_deleted == False,
    ]

    # 来源范围
    if search_range == "private":
        conditions.append(Question.source == "private")

    # 标签筛选
    if system_tag_ids:
        conditions.append(
            Question.id.in_(
                select(QuestionTag.question_id).where(
                    QuestionTag.system_tag_id.in_(system_tag_ids)
                )
            )
        )

    # 关键词条件
    kw_cond = _make_keyword_cond(keyword, search_scope)
    if kw_cond is not None:
        conditions.append(kw_cond)

    # 计数
    count_stmt = select(func.count()).select_from(Question).where(*conditions)
    total = (await db.execute(count_stmt)).scalar_one()

    # 分页 + 排序：有关键词时按相关性排序（ts_rank 优先），无关键词时按时间
    keyword = keyword.strip()
    if keyword:
        tsquery = func.plainto_tsquery(text("'simple'"), keyword)
        rank_expr = func.ts_rank(literal_column("content_tsv"), tsquery)
        if search_scope == "content_answer":
            rank_expr = func.greatest(
                rank_expr,
                func.ts_rank(literal_column("answer_tsv"), tsquery),
            )
        stmt = (
            select(Question, rank_expr.label("rank"))
            .where(*conditions)
            .order_by(literal_column("rank").desc(), Question.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        rows = result.all()
        questions = [row[0] for row in rows]
    else:
        stmt = (
            select(Question)
            .where(*conditions)
            .order_by(Question.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        questions = result.scalars().all()

    # 组装结果
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
