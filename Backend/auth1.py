"""backend/api/auth.py — Register, login, update profile"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, EmailStr
from backend.db.database import create_user, get_user_by_username, get_user_by_email, get_user_by_id, update_user
from backend.utils.auth  import hash_password, verify_password, create_token, current_user_id
from backend.utils.images import save_avatar

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterBody(BaseModel):
    username:  str
    email:     str
    password:  str
    full_name: str = ""


class LoginBody(BaseModel):
    username: str
    password: str


@router.post("/register", status_code=201)
async def register(body: RegisterBody):
    body.username = body.username.strip().lower()
    if len(body.username) < 3:
        raise HTTPException(400, "Username must be at least 3 characters")
    if await get_user_by_username(body.username):
        raise HTTPException(409, "Username already taken")
    if await get_user_by_email(body.email):
        raise HTTPException(409, "Email already registered")
    if len(body.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    uid = await create_user(body.username, body.email, hash_password(body.password), body.full_name)
    token = create_token(uid, body.username)
    return {"token": token, "user_id": uid, "username": body.username}


@router.post("/login")
async def login(body: LoginBody):
    user = await get_user_by_username(body.username.strip().lower())
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(401, "Invalid username or password")
    token = create_token(user["id"], user["username"])
    return {"token": token, "user_id": user["id"], "username": user["username"],
            "avatar_url": user["avatar_url"], "full_name": user["full_name"]}


@router.get("/me")
async def me(uid: int = Depends(current_user_id)):
    user = await get_user_by_id(uid)
    if not user:
        raise HTTPException(404, "User not found")
    user.pop("password_hash", None)
    return user


@router.put("/profile")
async def update_profile(
    full_name: str = Form(""),
    bio:       str = Form(""),
    uid: int = Depends(current_user_id)
):
    await update_user(uid, full_name=full_name, bio=bio)
    return {"ok": True}


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    uid:  int = Depends(current_user_id)
):
    url = await save_avatar(file, uid)
    await update_user(uid, avatar_url=url)
    return {"avatar_url": url}