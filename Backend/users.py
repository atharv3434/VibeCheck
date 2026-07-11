"""backend/api/users.py"""
from fastapi import APIRouter, HTTPException, Depends
from backend.db.database import (
    get_user_by_username, get_user_by_id, user_stats,
    follow_user, unfollow_user, is_following,
    get_followers, get_following, get_user_posts, search_users,
    create_notification
)
from backend.utils.auth import current_user_id, optional_user_id

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/search")
async def search(q: str = "", uid=Depends(optional_user_id)):
    if not q.strip():
        return []
    return await search_users(q.strip())


@router.get("/{username}")
async def profile(username: str, viewer_id=Depends(optional_user_id)):
    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(404, "User not found")
    user.pop("password_hash", None)
    stats = await user_stats(user["id"])
    following = await is_following(viewer_id, user["id"]) if viewer_id else False
    posts = await get_user_posts(user["id"], viewer_id)
    return {**user, **stats, "is_following": following, "posts": posts}


@router.post("/{username}/follow")
async def follow(username: str, uid: int = Depends(current_user_id)):
    target = await get_user_by_username(username)
    if not target:
        raise HTTPException(404, "User not found")
    if target["id"] == uid:
        raise HTTPException(400, "Cannot follow yourself")
    already = await is_following(uid, target["id"])
    if already:
        await unfollow_user(uid, target["id"])
        return {"following": False}
    await follow_user(uid, target["id"])
    await create_notification(target["id"], uid, "follow")
    return {"following": True}


@router.get("/{username}/followers")
async def followers(username: str):
    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(404, "User not found")
    return await get_followers(user["id"])


@router.get("/{username}/following")
async def following(username: str):
    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(404, "User not found")
    return await get_following(user["id"])