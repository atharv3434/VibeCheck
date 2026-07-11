"""backend/api/stories.py"""
from fastapi import APIRouter, Depends, File, Form, UploadFile
from backend.db.database import create_story, get_stories_feed, view_story
from backend.utils.auth import current_user_id, optional_user_id
from backend.utils.images import save_upload

router = APIRouter(prefix="/api/stories", tags=["stories"])


@router.post("", status_code=201)
async def new_story(
    caption: str = Form(""),
    file: UploadFile = File(...),
    uid: int = Depends(current_user_id)
):
    url = await save_upload(file, "stories")
    sid = await create_story(uid, url, caption)
    return {"id": sid, "image_url": url}


@router.get("/feed")
async def stories_feed(uid: int = Depends(current_user_id)):
    return await get_stories_feed(uid)


@router.post("/{story_id}/view")
async def mark_viewed(story_id: int, uid: int = Depends(current_user_id)):
    await view_story(story_id, uid)
    return {"ok": True}


# ─────────────────────────────────────────────────────────────────────────────

"""backend/api/feed.py"""
from fastapi import APIRouter, Depends, Query
from backend.db.database import get_feed, get_explore_posts
from backend.utils.auth import current_user_id, optional_user_id

feed_router = APIRouter(prefix="/api", tags=["feed"])


@feed_router.get("/feed")
async def home_feed(
    limit: int = Query(20, le=50), offset: int = Query(0, ge=0),
    uid: int = Depends(current_user_id)
):
    posts = await get_feed(uid, limit, offset)
    return {"posts": posts, "total": len(posts)}


@feed_router.get("/explore")
async def explore(
    limit: int = Query(30, le=60), offset: int = Query(0, ge=0),
    viewer_id=Depends(optional_user_id)
):
    posts = await get_explore_posts(viewer_id, limit, offset)
    return {"posts": posts}


# ─────────────────────────────────────────────────────────────────────────────

"""backend/api/notifications.py"""
from fastapi import APIRouter, Depends
from backend.db.database import get_notifications, mark_notifications_read, unread_count
from backend.utils.auth import current_user_id

notif_router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@notif_router.get("")
async def notifications(uid: int = Depends(current_user_id)):
    notifs = await get_notifications(uid)
    await mark_notifications_read(uid)
    return {"notifications": notifs}


@notif_router.get("/unread")
async def unread(uid: int = Depends(current_user_id)):
    return {"count": await unread_count(uid)}