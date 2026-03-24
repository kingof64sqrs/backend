from __future__ import annotations

import os
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


@router.post("/avatar", response_model=UploadResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
) -> UploadResponse:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG/PNG/WEBP/GIF images are accepted")

    data = await file.read()
    if len(data) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Image must be under 5 MB")

    ext = (file.filename or "avatar.jpg").rsplit(".", 1)[-1].lower()
    filename = f"{user.id}_{uuid.uuid4().hex}.{ext}"
    dest = UPLOAD_DIR / filename
    dest.write_bytes(data)

    # Return a relative URL served by the /media/{filename} route below
    return UploadResponse(url=f"/media/{filename}")


@router.get("/media/{filename}", include_in_schema=False)
async def serve_media(filename: str, user=Depends(get_current_user)) -> FileResponse:
    path = UPLOAD_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(path))
