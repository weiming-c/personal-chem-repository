"""文件上传服务"""
import os
import uuid
from datetime import datetime

import aiofiles
from fastapi import UploadFile, HTTPException
from PIL import Image

from app.config import settings


def _allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    for img_type in settings.ALLOWED_IMAGE_TYPES:
        if ext in img_type:
            return True
    # jpg/jpeg/png/webp
    return ext in ("jpg", "jpeg", "png", "webp", "gif")


async def save_upload(file: UploadFile) -> str:
    """保存上传图片，返回相对路径 URL"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名为空")

    if not _allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型，允许: jpg, png, webp"
        )

    # 读取内容检查大小
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制（{settings.MAX_UPLOAD_SIZE // 1024 // 1024}MB）"
        )

    # 校验是否真实图片（可选：跳过验证避免性能损耗）
    try:
        from io import BytesIO
        img = Image.open(BytesIO(content))
        img.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="文件不是有效图片")

    await file.seek(0)

    # 生成保存路径 — 按日期分目录
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    date_dir = datetime.now().strftime("%Y/%m")
    save_dir = os.path.join(settings.UPLOAD_DIR, date_dir)
    os.makedirs(save_dir, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(save_dir, filename)

    # 异步写入
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(content)

    # 返回相对 URL（供前端访问 /uploads/...）
    return f"/uploads/{date_dir}/{filename}"
