"""题目管理 API 路由"""
from fastapi import APIRouter, Body, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.question import (
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    QuestionListItem,
    OCRRequest,
    OCRResponse,
)
from app.services.question import (
    create_question,
    get_question,
    list_questions,
    update_question,
    delete_question,
)
from app.services.ocr import recognize_image
from app.utils.response import success, paginated, error

router = APIRouter(prefix="/api/questions", tags=["题目"])


@router.post("")
async def api_create_question(
    content: str = Form(..., description="题干文本"),
    answer: str | None = Form(None, description="答案文本"),
    note: str | None = Form(None, description="备注"),
    source: str = Form("private", description="来源"),
    system_tag_ids: str = Form("", description="系统标签ID（逗号分隔）"),
    user_tag_ids: str = Form("", description="自定义标签ID（逗号分隔）"),
    user_tag_names: str = Form("", description="新建自定义标签名（逗号分隔）"),
    image_url: str | None = Form(None, description="图片URL（已上传获得）"),
    image: UploadFile | None = File(None, description="题目图片文件（可选直接上传）"),
    db: AsyncSession = Depends(get_db),
):
    """创建题目 — 支持图片上传 + 标签"""
    def parse_ids(s: str) -> list[int]:
        if not s.strip():
            return []
        return [int(x.strip()) for x in s.split(",") if x.strip()]

    def parse_names(s: str) -> list[str]:
        if not s.strip():
            return []
        return [x.strip() for x in s.split(",") if x.strip()]

    data = QuestionCreate(
        content=content,
        answer=answer,
        note=note,
        source=source,
        system_tag_ids=parse_ids(system_tag_ids),
        user_tag_ids=parse_ids(user_tag_ids),
        user_tag_names=parse_names(user_tag_names),
    )

    result = await create_question(db, data, image_url, image)
    return success(data=result.model_dump(), message="题目创建成功")


@router.put("/{question_id}")
async def api_update_question(
    question_id: int,
    data: QuestionUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """更新题目"""
    result = await update_question(db, question_id, data)
    return success(data=result.model_dump(), message="题目更新成功")


@router.get("/{question_id}")
async def api_get_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取题目详情"""
    result = await get_question(db, question_id)
    return success(data=result.model_dump())


@router.get("")
async def api_list_questions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: str | None = Query(None),
    system_tag_id: int | None = Query(None),
    user_tag_id: int | None = Query(None),
    keyword: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """分页查询题目列表"""
    items, total = await list_questions(
        db,
        page=page,
        page_size=page_size,
        source=source,
        system_tag_id=system_tag_id,
        user_tag_id=user_tag_id,
        keyword=keyword,
    )
    return paginated(
        data=[item.model_dump() for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/{question_id}")
async def api_delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除题目（软删除）"""
    await delete_question(db, question_id)
    return success(message="题目已删除")


# ---------- OCR ----------
from pydantic import BaseModel

class OcrImageUrlRequest(BaseModel):
    imageUrl: str

router_ocr = APIRouter(prefix="/api/ocr", tags=["OCR"])


@router_ocr.post("/recognize")
async def api_ocr_recognize(
    request: OcrImageUrlRequest = Body(...),
):
    """OCR 识别接口 — 传入图片URL，返回识别的题干和答案"""
    if not request.imageUrl:
        from app.utils.response import error
        return error(code=400, message="请提供图片URL")

    result = await recognize_image(request.imageUrl)
    return success(data=result.model_dump())


# ---------- 文件上传 ----------
router_upload = APIRouter(prefix="/api", tags=["上传"])


@router_upload.post("/upload")
async def api_upload_image(
    file: UploadFile = File(..., description="图片文件"),
):
    """独立图片上传接口 — 返回图片URL"""
    from app.services.upload import save_upload
    url = await save_upload(file)
    return success(data={"url": url}, message="上传成功")
