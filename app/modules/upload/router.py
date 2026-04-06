from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.auth import get_current_user

UPLOAD_DIR = Path("/tmp/aroundyou_media")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

router = APIRouter(prefix="/upload", tags=["upload"])


class UploadResponse(BaseModel):
    url: str


def _build_media_url(filename: str) -> str:
    # Router is mounted at /api/v1/upload in app.main
    return f"/api/v1/upload/media/{filename}"


def _validate_image_upload(file: UploadFile, data: bytes) -> None:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG/PNG/WEBP/GIF images are accepted")
    if len(data) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Image must be under 5 MB")


def _store_file(user_id: str, filename: str, data: bytes) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    safe_name = f"{user_id}_{uuid.uuid4().hex}.{ext}"
    dest = UPLOAD_DIR / safe_name
    dest.write_bytes(data)
    return safe_name


@router.post("/avatar", response_model=UploadResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
) -> UploadResponse:
    data = await file.read()
    _validate_image_upload(file, data)

    filename = _store_file(user.id, file.filename or "avatar.jpg", data)
    return UploadResponse(url=_build_media_url(filename))


@router.post("/post-media", response_model=UploadResponse)
async def upload_post_media(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
) -> UploadResponse:
    data = await file.read()
    _validate_image_upload(file, data)

    filename = _store_file(user.id, file.filename or "post.jpg", data)
    return UploadResponse(url=_build_media_url(filename))


@router.get("/media/{filename}", include_in_schema=False)
async def serve_media(filename: str) -> FileResponse:
    path = UPLOAD_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(path))
