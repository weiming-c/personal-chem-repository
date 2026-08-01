"""图片增强服务

实现"扫描全能王"式图片增强流水线：

    前端框四角(归一化坐标) → OpenCV 透视矫正 → Pillow 压缩后处理 → JPEG

流程要点：
- 四角坐标顺序约定：[左上, 右上, 右下, 左下]，均为 0~1 归一化值。
- 矫正必须先于压缩（透视变换会改变像素坐标，压缩会丢失信息）。
- 任何一步失败都回退返回原图字节，绝不让上传流程因增强失败而中断。
"""

import json
import logging
from io import BytesIO

from app.config import settings

logger = logging.getLogger(__name__)

# 四角归一化坐标的默认贴角值（与前端画布默认一致）
_DEFAULT_CORNERS = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]


class EnhanceError(Exception):
    """图片增强失败（内部异常，不向上抛出）"""


# ---------- 四角坐标解析与校验 ----------

def parse_corners(corners_str: str | None) -> list[tuple[float, float]] | None:
    """解析并校验前端传来的四角坐标 JSON 字符串。

    输入示例: `[{"x":0,"y":0},{"x":1,"y":0},{"x":1,"y":1},{"x":0,"y":1}]`

    返回 [(x, y) * 4]，顺序为 [左上, 右上, 右下, 左下]；
    任何非法输入（非JSON、不是4个点、坐标越界）返回 None，调用方据此跳过矫正。
    """
    if not corners_str:
        return None
    try:
        raw = json.loads(corners_str)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(raw, list) or len(raw) != 4:
        return None

    corners: list[tuple[float, float]] = []
    for p in raw:
        if not isinstance(p, dict):
            return None
        x, y = p.get("x"), p.get("y")
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            return None
        x, y = float(x), float(y)
        # 归一化坐标必须在 0~1 范围
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            return None
        corners.append((x, y))
    return corners


def _is_near_default(corners: list[tuple[float, float]]) -> bool:
    """判断四角是否基本等于默认贴角（用户未拖动），此时无需透视矫正，仅做压缩。"""
    return all(
        abs(x - dx) < 0.01 and abs(y - dy) < 0.01
        for (x, y), (dx, dy) in zip(corners, _DEFAULT_CORNERS)
    )


# ---------- 透视矫正（OpenCV） ----------

def _warp_perspective(content: bytes, corners: list[tuple[float, float]]) -> bytes:
    """OpenCV 透视矫正：将四角区域拉正为矩形，返回 PNG 字节。"""
    import cv2
    import numpy as np

    arr = np.frombuffer(content, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise EnhanceError("无法解码图片")

    h, w = img.shape[:2]

    # 源点：归一化坐标 → 像素坐标（左上、右上、右下、左下）
    src = np.array([[x * w, y * h] for x, y in corners], dtype=np.float32)

    # 目标矩形尺寸：取上下边宽、左右边高的最大值，避免目标小于内容
    w_top = float(np.linalg.norm(src[1] - src[0]))
    w_bottom = float(np.linalg.norm(src[2] - src[3]))
    h_left = float(np.linalg.norm(src[3] - src[0]))
    h_right = float(np.linalg.norm(src[2] - src[1]))
    dst_w = max(1, int(round(max(w_top, w_bottom))))
    dst_h = max(1, int(round(max(h_left, h_right))))

    dst = np.array(
        [[0, 0], [dst_w - 1, 0], [dst_w - 1, dst_h - 1], [0, dst_h - 1]],
        dtype=np.float32,
    )

    matrix = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(
        img,
        matrix,
        (dst_w, dst_h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,  # 边缘外扩填充，避免黑边
    )
    ok, encoded = cv2.imencode(".png", warped)
    if not ok:
        raise EnhanceError("矫正后编码失败")
    return encoded.tobytes()


# ---------- 压缩后处理（Pillow） ----------

def _post_process(content: bytes) -> bytes:
    """Pillow 后处理：缩放长边 + 增白 + 锐化 → JPEG 字节。"""
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps

    img = Image.open(BytesIO(content))
    img = img.convert("RGB")  # 统一 RGB，保证 JPEG 可保存

    # 1. 缩放长边到配置值（默认 1600px）
    max_edge = settings.ENHANCED_MAX_EDGE
    if max(img.size) > max_edge:
        img.thumbnail((max_edge, max_edge), Image.LANCZOS)

    # 2. 增白：自动对比度 + 轻微提亮，模拟"扫描全能王"去灰增白
    img = ImageOps.autocontrast(img, cutoff=1)
    img = ImageEnhance.Brightness(img).enhance(1.02)

    # 3. 锐化：让文字/结构式线条更清晰
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=80, threshold=3))

    buf = BytesIO()
    img.save(
        buf,
        "JPEG",
        quality=settings.ENHANCED_JPEG_QUALITY,
        optimize=True,
    )
    return buf.getvalue()


# ---------- 对外主入口 ----------

def enhance_image(content: bytes, corners: list[tuple[float, float]]) -> tuple[bytes, bool]:
    """执行图片增强流水线（同步函数，应在线程池中调用）。

    参数:
        content: 原始图片字节
        corners: 已通过 parse_corners 校验的四角归一化坐标

    返回:
        (增强后图片字节, 是否执行了增强)。增强失败时返回 (原图字节, False)。
    """
    if not settings.IMAGE_ENHANCE_ENABLED or not corners:
        return content, False

    try:
        if _is_near_default(corners):
            # 用户未拖动四角：仅做压缩后处理，不做透视矫正（避免无意义的变换误差）
            return _post_process(content), True
        warped = _warp_perspective(content, corners)
        return _post_process(warped), True
    except Exception as e:
        logger.warning("图片增强失败，回退原图: %s", e)
        return content, False
