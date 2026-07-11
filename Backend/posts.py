"""backend/api/posts.py — Create, get, delete posts; likes; comments"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from backend.db.database import (
    create_post, get_post, delete_post, get_user_posts,
    toggle_like, add_comment, get_comments, delete_comment,
    get_user_by_id, create_notification
)
from backend.utils.auth   import current_user_id, optional_user_id
from backend.utils.images import save_upload

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.post("", status_code=201)
async def new_post(
    caption:  str = Form(""),
    location: str = Form(""),
    file: UploadFile = File(...),
    uid:  int = Depends(current_user_id)
):
    url     = await save_upload(file, "posts")
    post_id = await create_post(uid, url, caption, location)
    return {"id": post_id, "image_url": url, "caption": caption}


@router.get("/{post_id}")
async def get_single_post(post_id: int, viewer_id=Depends(optional_user_id)):
    post = await get_post(post_id, viewer_id)
    if not post:
        raise HTTPException(404, "Post not found")
    return post


@router.delete("/{post_id}")
async def remove_post(post_id: int, uid: int = Depends(current_user_id)):
    post = await get_post(post_id)
    if not post:
        raise HTTPException(404, "Post not found")
    if post["user_id"] != uid:
        raise HTTPException(403, "Not your post")
    await delete_post(post_id, uid)
    return {"ok": True}


@router.post("/{post_id}/like")
async def like_post(post_id: int, uid: int = Depends(current_user_id)):
    post = await get_post(post_id)
    if not post:
        raise HTTPException(404, "Post not found")
    liked = await toggle_like(uid, post_id)
    if liked:
        await create_notification(post["user_id"], uid, "like", post_id)
    return {"liked": liked}


@router.get("/{post_id}/comments")
async def list_comments(post_id: int):
    return await get_comments(post_id)


class CommentBody(BaseModel):
    text: str


@router.post("/{post_id}/comments", status_code=201)
async def new_comment(post_id: int, body: CommentBody, uid: int = Depends(current_user_id)):
    if not body.text.strip():
        raise HTTPException(400, "Comment cannot be empty")
    post = await get_post(post_id)
    if not post:
        raise HTTPException(404, "Post not found")
    cid = await add_comment(post_id, uid, body.text.strip())
    await create_notification(post["user_id"], uid, "comment", post_id)
    user = await get_user_by_id(uid)
    return {"id": cid, "text": body.text, "username": user["username"], "avatar_url": user["avatar_url"]}


@router.delete("/comments/{comment_id}")
async def remove_comment(comment_id: int, uid: int = Depends(current_user_id)):
    await delete_comment(comment_id, uid)
    return {"ok": True}