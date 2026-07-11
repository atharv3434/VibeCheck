"""main.py — Photogram FastAPI application"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

from backend.db.database import init_db
from backend.api.auth    import router as auth_router
from backend.api.posts   import router as posts_router
from backend.api.users   import router as users_router
from backend.api.feed_stories_notif import router as stories_router, feed_router, notif_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    for d in ["uploads/posts", "uploads/stories", "uploads/avatars"]:
        os.makedirs(d, exist_ok=True)
    await init_db()
    print("\n✅ Photogram ready → http://localhost:8000\n")
    yield


app = FastAPI(title="Photogram", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

for r in [auth_router, posts_router, users_router, stories_router, feed_router, notif_router]:
    app.include_router(r)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static",  StaticFiles(directory="frontend/static"), name="static")

templates = Jinja2Templates(directory="frontend/templates")


@app.get("/{full_path:path}", response_class=HTMLResponse)
async def spa(request: Request, full_path: str):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)