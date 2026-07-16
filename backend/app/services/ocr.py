"""OCR 识别服务

当前阶段提供桩实现。后续替换为真实 PaddleOCR / Tesseract OCR 集成。
"""

from app.schemas.question import OCRResponse


async def recognize_image(image_url: str, image_type: str = "question") -> OCRResponse:
    """
    对图片进行 OCR 识别，提取题干和答案文本。

    当前桩实现：返回占位文本提示用户手动输入。
    后续接入 OCR 时替换此处逻辑即可。

    image_type: "question" = 题干图, "answer" = 答案图
    """
    if image_type == "answer":
        return OCRResponse(
            content="（OCR 识别结果 — 请在此处粘贴或手动输入答案文本）",
            answer="",
            raw_text="",
        )
    return OCRResponse(
        content="（OCR 识别结果 — 请在此处粘贴或手动输入题干文本）",
        answer="",
        raw_text="",
    )


async def recognize_image_with_answer(image_url: str) -> OCRResponse:
    """
    识别图片并尝试拆分为题干和答案。
    桩实现。
    """
    return await recognize_image(image_url)
