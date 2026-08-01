"""文件上传服务"""
import asyncio
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO

import aiofiles
from fastapi import UploadFile, HTTPException
from PIL import Image

from app.config import settings
from app.services.image_enhance import enhance_image, parse_corners


@dataclass
class UploadResult:
    """上传结果

    - url: 最终可用的图片 URL（增强成功后为增强图，否则为原图）
    - raw_image_url: 原图备份 URL（增强成功且 KEEP_RAW_IMAGE=True 时返回）
    - enhanced: 是否执行了增强流水线
    """

    url: str
    raw_image_url: str | None = None
    enhanced: bool = False

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "rawImageUrl": self.raw_image_url,
            "enhanced": self.enhanced,
        }


def _allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    for img_type in settings.ALLOWED_IMAGE_TYPES:
        if ext in img_type:
            return True
    # jpg/jpeg/png/webp
    return ext in ("jpg", "jpeg", "png", "webp", "gif")


async def _write_bytes(content: bytes, ext: str) -> str:
    """按日期分目录写入字节，返回相对 URL"""
    date_dir = datetime.now().strftime("%Y/%m")
    save_dir = os.path.join(settings.UPLOAD_DIR, date_dir)
    os.makedirs(save_dir, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(save_dir, filename)

    async with aiofiles.open(save_path, "wb") as f:
        await f.write(content)

    return f"/uploads/{date_dir}/{filename}"


async def save_upload(file: UploadFile, corners: str | None = None) -> UploadResult:
    """保存上传图片，可选执行"框四角 + 透视矫正 + 压缩"增强流水线。

    参数:
        file: 上传文件
        corners: 四角归一化坐标的 JSON 字符串（`[{"x":0,"y":0},...]`，4 个点）
                 由前端画布生成；缺省或非法时跳过增强，直接存原图。

    返回:
        UploadResult：增强后图片 URL + 原图备份 URL + 是否增强
    """
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
        img = Image.open(BytesIO(content))
        img.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="文件不是有效图片")

    await file.seek(0)

    # 解析四角坐标（非法返回 None → 不增强）
    corner_points = parse_corners(corners)

    # 1) 增强流水线（OpenCV 为 CPU 密集型，放到线程池避免阻塞事件循环）
    enhanced_content = content
    enhanced = False
    if corner_points is not None:
        loop = asyncio.get_running_loop()
        enhanced_content, enhanced = await loop.run_in_executor(
            None, enhance_image, content, corner_points
        )

    # 2) 保存原图备份（增强图沿用原扩展名，若增强则另存 JPEG）
    raw_url = await _write_bytes(content, _original_ext(file.filename))

    if enhanced:
        # 增强结果统一为 JPEG
        enhanced_url = await _write_bytes(enhanced_content, "jpg")
        if settings.KEEP_RAW_IMAGE:
            return UploadResult(url=enhanced_url, raw_image_url=raw_url, enhanced=True)
        # 不保留原图：删除已保存的原图文件，仅保留增强图
        raw_path = os.path.join(settings.UPLOAD_DIR, raw_url.lstrip("/uploads/"))
        try:
            os.remove(raw_path)
        except OSError:
            pass
        return UploadResult(url=enhanced_url, enhanced=True)

    return UploadResult(url=raw_url, enhanced=False)


def _original_ext(filename: str) -> str:
    """提取原始扩展名，未知/异常时回退 jpg"""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext if ext in ("jpg", "jpeg", "png", "webp", "gif") else "jpg"
