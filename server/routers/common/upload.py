"""文件上传 — 图片存储，返回访问URL"""
import uuid
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from auth import get_current_user
from config import settings

router = APIRouter(prefix="/api/common/upload", tags=["公共-上传"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("")
def upload_image(
    file: UploadFile = File(...),
    _=Depends(get_current_user),  # 需要登录
):
    """上传图片，返回访问 URL"""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="仅支持 jpeg/png/gif/webp 格式")

    content = file.file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="图片最大 5MB")

    ext = os.path.splitext(file.filename or ".png")[1] or ".png"
    filename = f"{uuid.uuid4().hex}{ext}"

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / filename).write_bytes(content)

    return {"url": f"/uploads/{filename}", "filename": filename}
