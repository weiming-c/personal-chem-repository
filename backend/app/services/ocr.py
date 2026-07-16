"""OCR 识别服务

基于 RapidOCR (ONNX Runtime) 实现，使用 PaddleOCR 的中文识别模型。
无需安装 PaddlePaddle，轻量高效，中文准确度高。
"""

import os
import asyncio
import tempfile
import logging
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import aiohttp
import aiofiles

from app.config import settings
from app.schemas.question import OCRResponse

logger = logging.getLogger(__name__)

# 线程池用于执行 CPU 密集型 OCR 任务
_ocr_executor = ThreadPoolExecutor(max_workers=1)
_engine = None


def _get_engine():
    """获取 RapidOCR 引擎单例（惰性加载）"""
    global _engine
    if _engine is None:
        from rapidocr_onnxruntime import RapidOCR
        import sys
        print("正在初始化 RapidOCR...", file=sys.stderr, flush=True)
        # box_thresh 提高过滤阈值，unclip_ratio 缩小文本框，加速检测
        _engine = RapidOCR(det_box_thresh=0.4, det_unclip_ratio=1.5)
        print("RapidOCR 初始化完成", file=sys.stderr, flush=True)
    return _engine


def _is_local_path(image_url: str) -> bool:
    """判断是否为本地路径（/uploads/...）"""
    parsed = urlparse(image_url)
    return not parsed.scheme or image_url.startswith("/")


def _resolve_path(image_url: str) -> str:
    """将相对 URL 转换为绝对文件路径
    例如: /uploads/2026/07/xxx.png -> {UPLOAD_DIR}/2026/07/xxx.png
    """
    rel = image_url.lstrip("/")
    if rel.startswith("uploads/"):
        rel = rel[len("uploads/"):]
    return os.path.join(settings.UPLOAD_DIR, rel)


async def _download_image(image_url: str) -> str:
    """下载远程图片到临时文件，返回临时文件路径"""
    suffix = ".jpg"
    if image_url.lower().endswith(".png"):
        suffix = ".png"
    elif image_url.lower().endswith(".webp"):
        suffix = ".webp"

    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)

    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as resp:
            if resp.status != 200:
                raise RuntimeError(f"下载图片失败: HTTP {resp.status}")
            data = await resp.read()
            async with aiofiles.open(tmp_path, "wb") as f:
                await f.write(data)

    return tmp_path


def _run_ocr(img_path: str) -> str:
    """同步执行 OCR 识别，返回合并的文本（在多线程中运行）"""
    engine = _get_engine()
    result, _ = engine(img_path)
    if not result:
        return ""
    lines = [text for _, text, conf in result if text and text.strip()]
    return "\n".join(lines)


async def recognize_image(image_url: str, image_type: str = "question") -> OCRResponse:
    """
    对图片进行 OCR 识别，提取文本。

    image_type: "question" = 题干图, "answer" = 答案图
    """
    import sys
    img_path = None
    is_temp = False

    try:
        print(f"OCR 请求: url={image_url}, type={image_type}", file=sys.stderr, flush=True)
        # 解析图片路径
        if _is_local_path(image_url):
            img_path = _resolve_path(image_url)
            print(f"  本地路径: {img_path}, exists={os.path.isfile(img_path)}", file=sys.stderr, flush=True)
            if not os.path.isfile(img_path):
                raise FileNotFoundError(f"图片文件不存在: {img_path}")
        else:
            print(f"  远程URL, 开始下载...", file=sys.stderr, flush=True)
            img_path = await _download_image(image_url)
            is_temp = True
            print(f"  下载完成: {img_path}", file=sys.stderr, flush=True)

        # 在线程池中执行 OCR（避免阻塞 event loop）
        loop = asyncio.get_running_loop()
        print(f"  开始OCR识别...", file=sys.stderr, flush=True)
        full_text = await loop.run_in_executor(_ocr_executor, _run_ocr, img_path)
        print(f"  OCR结果 chars={len(full_text)}, preview='{full_text[:50]}...'", file=sys.stderr, flush=True)

        if not full_text.strip():
            print(f"  识别为空", file=sys.stderr, flush=True)
            return OCRResponse(
                content="（未能识别到文字，请手动输入）",
                answer="",
                raw_text="",
            )

        return OCRResponse(
            content=full_text,
            answer="",
            raw_text=full_text,
        )

    except FileNotFoundError:
        import traceback
        print(f"  文件不存在: {traceback.format_exc()}", file=sys.stderr, flush=True)
        return OCRResponse(
            content="（图片文件未找到，请重新上传）",
            answer="",
            raw_text="",
        )
    except Exception as e:
        import traceback
        print(f"  OCR异常: {traceback.format_exc()}", file=sys.stderr, flush=True)
        return OCRResponse(
            content="（OCR 识别失败，请手动输入）",
            answer="",
            raw_text="",
        )
    finally:
        if is_temp and img_path and os.path.isfile(img_path):
            os.unlink(img_path)


async def recognize_image_with_answer(image_url: str) -> OCRResponse:
    """
    识别图片并尝试拆分为题干和答案。
    目前直接返回全文识别结果。
    """
    return await recognize_image(image_url)
