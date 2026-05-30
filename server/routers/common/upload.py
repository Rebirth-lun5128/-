"""文件上传 — 图片存储，返回访问URL。包含真实图片内容校验"""
import io
import uuid
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from PIL import Image, UnidentifiedImageError

from auth import get_current_user
from config import settings
from ratelimit import strict_limiter

router = APIRouter(prefix="/api/common/upload", tags=["公共-上传"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("")
def upload_image(
    file: UploadFile = File(...),
    _user=Depends(get_current_user),  # 需要登录
    _rl=Depends(strict_limiter),  # 上传限流
):
    """上传图片，返回访问 URL。校验真实图片内容防止伪造 MIME"""
    # 读取文件内容
    content = file.file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="图片最大 5MB")

    # 使用 Pillow 验证是否为真实图片（防 MIME 伪造）
    try:
        img = Image.open(io.BytesIO(content))
        img.verify()  # 验证图片完整性，不加载像素数据
        # verify() 后需重新打开才能读格式
        img = Image.open(io.BytesIO(content))
        fmt = (img.format or "PNG").upper()
    except (UnidentifiedImageError, Exception):
        raise HTTPException(status_code=400, detail="无法识别的图片格式，请上传真实图片")

    # 根据实际图片格式确定扩展名
    fmt_to_ext = {"JPEG": ".jpg", "JPG": ".jpg", "PNG": ".png", "GIF": ".gif", "WEBP": ".webp"}
    ext = fmt_to_ext.get(fmt, ".png")
    filename = f"{uuid.uuid4().hex}{ext}"

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / filename).write_bytes(content)

    return {"url": f"/uploads/{filename}", "filename": filename}
