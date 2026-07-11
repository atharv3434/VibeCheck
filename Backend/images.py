"""backend/utils/images.py — Image upload, validation, resizing"""
import os, uuid, aiofiles
from fastapi import UploadFile, HTTPException
from PIL import Image
import io

UPLOAD_DIR   = "uploads"
MAX_SIZE_MB  = 10
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_DIMENSION = 1080


async def save_upload(file: UploadFile, folder: str) -> str:
    """Save an uploaded image, validate & resize it. Returns relative URL."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    contents = await file.read()
    if len(contents) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large (max {MAX_SIZE_MB}MB)")

    # Validate & resize with Pillow
    try:
        img = Image.open(io.BytesIO(contents))
        img.verify()
        img = Image.open(io.BytesIO(contents))   # reopen after verify
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        contents = buf.getvalue()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}")

    ext      = "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    dir_path = os.path.join(UPLOAD_DIR, folder)
    os.makedirs(dir_path, exist_ok=True)
    path = os.path.join(dir_path, filename)

    async with aiofiles.open(path, "wb") as f:
        await f.write(contents)

    return f"/uploads/{folder}/{filename}"


async def save_avatar(file: UploadFile, user_id: int) -> str:
    """Save & crop avatar to square 400×400."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    contents = await file.read()
    try:
        img = Image.open(io.BytesIO(contents))
        img = img.convert("RGB")
        # Crop to square
        w, h = img.size
        side  = min(w, h)
        left  = (w - side) // 2
        top   = (h - side) // 2
        img   = img.crop((left, top, left+side, top+side))
        img   = img.resize((400, 400), Image.LANCZOS)
        buf   = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        contents = buf.getvalue()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}")

    filename = f"avatar_{user_id}.jpg"
    dir_path = os.path.join(UPLOAD_DIR, "avatars")
    os.makedirs(dir_path, exist_ok=True)
    path = os.path.join(dir_path, filename)

    async with aiofiles.open(path, "wb") as f:
        await f.write(contents)

    return f"/uploads/avatars/{filename}"