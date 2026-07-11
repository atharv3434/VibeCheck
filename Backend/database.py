"""
backend/db/database.py  —  SQLite schema + async query helpers
"""

import aiosqlite, time, os

DB_PATH = os.getenv("DB_PATH", "photogram.db")

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    username     TEXT UNIQUE NOT NULL,
    email        TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name    TEXT DEFAULT '',
    bio          TEXT DEFAULT '',
    avatar_url   TEXT DEFAULT '/static/img/default_avatar.svg',
    is_private   INTEGER DEFAULT 0,
    created_at   REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS follows (
    follower_id  INTEGER NOT NULL,
    following_id INTEGER NOT NULL,
    created_at   REAL NOT NULL,
    PRIMARY KEY (follower_id, following_id),
    FOREIGN KEY (follower_id)  REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS posts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    image_url    TEXT NOT NULL,
    caption      TEXT DEFAULT '',
    location     TEXT DEFAULT '',
    created_at   REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS likes (
    user_id  INTEGER NOT NULL,
    post_id  INTEGER NOT NULL,
    created_at REAL NOT NULL,
    PRIMARY KEY (user_id, post_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id    INTEGER NOT NULL,
    user_id    INTEGER NOT NULL,
    text       TEXT NOT NULL,
    created_at REAL NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS stories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    image_url   TEXT NOT NULL,
    caption     TEXT DEFAULT '',
    expires_at  REAL NOT NULL,
    created_at  REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS story_views (
    story_id   INTEGER NOT NULL,
    viewer_id  INTEGER NOT NULL,
    viewed_at  REAL NOT NULL,
    PRIMARY KEY (story_id, viewer_id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    actor_id    INTEGER NOT NULL,
    type        TEXT NOT NULL,
    ref_id      INTEGER,
    is_read     INTEGER DEFAULT 0,
    created_at  REAL NOT NULL,
    FOREIGN KEY (user_id)  REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS hashtags (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS post_hashtags (
    post_id    INTEGER NOT NULL,
    hashtag_id INTEGER NOT NULL,
    PRIMARY KEY (post_id, hashtag_id)
);

CREATE INDEX IF NOT EXISTS idx_posts_user    ON posts(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_time    ON posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_likes_post    ON likes(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_stories_user  ON stories(user_id);
CREATE INDEX IF NOT EXISTS idx_notifs_user   ON notifications(user_id);
"""


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


# ── Users ─────────────────────────────────────────────────────────────────────

async def create_user(username, email, password_hash, full_name=""):
    async with await get_db() as db:
        cur = await db.execute(
            "INSERT INTO users (username,email,password_hash,full_name,created_at) VALUES (?,?,?,?,?)",
            (username, email, password_hash, full_name, time.time()))
        await db.commit()
        return cur.lastrowid


async def get_user_by_id(uid):
    async with await get_db() as db:
        row = await db.execute_fetchone("SELECT * FROM users WHERE id=?", (uid,))
        return dict(row) if row else None


async def get_user_by_username(username):
    async with await get_db() as db:
        row = await db.execute_fetchone("SELECT * FROM users WHERE username=?", (username,))
        return dict(row) if row else None


async def get_user_by_email(email):
    async with await get_db() as db:
        row = await db.execute_fetchone("SELECT * FROM users WHERE email=?", (email,))
        return dict(row) if row else None


async def update_user(uid, **kwargs):
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [uid]
    async with await get_db() as db:
        await db.execute(f"UPDATE users SET {fields} WHERE id=?", values)
        await db.commit()


async def user_stats(uid):
    async with await get_db() as db:
        posts = (await db.execute_fetchone("SELECT COUNT(*) as c FROM posts WHERE user_id=?", (uid,)))["c"]
        followers = (await db.execute_fetchone("SELECT COUNT(*) as c FROM follows WHERE following_id=?", (uid,)))["c"]
        following = (await db.execute_fetchone("SELECT COUNT(*) as c FROM follows WHERE follower_id=?", (uid,)))["c"]
        return {"posts": posts, "followers": followers, "following": following}


async def search_users(query, limit=20):
    async with await get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT id,username,full_name,avatar_url FROM users WHERE username LIKE ? OR full_name LIKE ? LIMIT ?",
            (f"%{query}%", f"%{query}%", limit))
        return [dict(r) for r in rows]


# ── Follows ───────────────────────────────────────────────────────────────────

async def follow_user(follower_id, following_id):
    async with await get_db() as db:
        try:
            await db.execute("INSERT INTO follows VALUES (?,?,?)", (follower_id, following_id, time.time()))
            await db.commit()
            return True
        except Exception:
            return False


async def unfollow_user(follower_id, following_id):
    async with await get_db() as db:
        await db.execute("DELETE FROM follows WHERE follower_id=? AND following_id=?", (follower_id, following_id))
        await db.commit()


async def is_following(follower_id, following_id):
    async with await get_db() as db:
        row = await db.execute_fetchone(
            "SELECT 1 FROM follows WHERE follower_id=? AND following_id=?", (follower_id, following_id))
        return row is not None


async def get_followers(uid, limit=50):
    async with await get_db() as db:
        rows = await db.execute_fetchall(
            """SELECT u.id,u.username,u.full_name,u.avatar_url
               FROM follows f JOIN users u ON u.id=f.follower_id
               WHERE f.following_id=? ORDER BY f.created_at DESC LIMIT ?""", (uid, limit))
        return [dict(r) for r in rows]


async def get_following(uid, limit=50):
    async with await get_db() as db:
        rows = await db.execute_fetchall(
            """SELECT u.id,u.username,u.full_name,u.avatar_url
               FROM follows f JOIN users u ON u.id=f.following_id
               WHERE f.follower_id=? ORDER BY f.created_at DESC LIMIT ?""", (uid, limit))
        return [dict(r) for r in rows]


# ── Posts ─────────────────────────────────────────────────────────────────────

async def create_post(user_id, image_url, caption="", location=""):
    async with await get_db() as db:
        cur = await db.execute(
            "INSERT INTO posts (user_id,image_url,caption,location,created_at) VALUES (?,?,?,?,?)",
            (user_id, image_url, caption, location, time.time()))
        await db.commit()
        return cur.lastrowid


async def get_post(post_id, viewer_id=None):
    async with await get_db() as db:
        row = await db.execute_fetchone("""
            SELECT p.*, u.username, u.avatar_url, u.full_name,
                   (SELECT COUNT(*) FROM likes WHERE post_id=p.id) as like_count,
                   (SELECT COUNT(*) FROM comments WHERE post_id=p.id) as comment_count
                   {liked}
            FROM posts p JOIN users u ON u.id=p.user_id
            WHERE p.id=?
        """.replace("{liked}",
            f", (SELECT COUNT(*) FROM likes WHERE post_id=p.id AND user_id={viewer_id}) as is_liked"
            if viewer_id else ", 0 as is_liked"), (post_id,))
        return dict(row) if row else None


async def delete_post(post_id, user_id):
    async with await get_db() as db:
        await db.execute("DELETE FROM posts WHERE id=? AND user_id=?", (post_id, user_id))
        await db.commit()


async def get_user_posts(uid, viewer_id=None, limit=30, offset=0):
    async with await get_db() as db:
        liked_sub = f"(SELECT COUNT(*) FROM likes WHERE post_id=p.id AND user_id={viewer_id}) as is_liked" \
                    if viewer_id else "0 as is_liked"
        rows = await db.execute_fetchall(f"""
            SELECT p.*, u.username, u.avatar_url,
                   (SELECT COUNT(*) FROM likes WHERE post_id=p.id) as like_count,
                   (SELECT COUNT(*) FROM comments WHERE post_id=p.id) as comment_count,
                   {liked_sub}
            FROM posts p JOIN users u ON u.id=p.user_id
            WHERE p.user_id=? ORDER BY p.created_at DESC LIMIT ? OFFSET ?
        """, (uid, limit, offset))
        return [dict(r) for r in rows]


async def get_feed(user_id, limit=30, offset=0):
    async with await get_db() as db:
        rows = await db.execute_fetchall(f"""
            SELECT p.*, u.username, u.avatar_url, u.full_name,
                   (SELECT COUNT(*) FROM likes WHERE post_id=p.id) as like_count,
                   (SELECT COUNT(*) FROM comments WHERE post_id=p.id) as comment_count,
                   (SELECT COUNT(*) FROM likes WHERE post_id=p.id AND user_id={user_id}) as is_liked
            FROM posts p JOIN users u ON u.id=p.user_id
            WHERE p.user_id IN (SELECT following_id FROM follows WHERE follower_id=?)
               OR p.user_id=?
            ORDER BY p.created_at DESC LIMIT ? OFFSET ?
        """, (user_id, user_id, limit, offset))
        return [dict(r) for r in rows]


async def get_explore_posts(viewer_id=None, limit=30, offset=0):
    async with await get_db() as db:
        liked_sub = f"(SELECT COUNT(*) FROM likes WHERE post_id=p.id AND user_id={viewer_id}) as is_liked" \
                    if viewer_id else "0 as is_liked"
        rows = await db.execute_fetchall(f"""
            SELECT p.*, u.username, u.avatar_url,
                   (SELECT COUNT(*) FROM likes WHERE post_id=p.id) as like_count,
                   (SELECT COUNT(*) FROM comments WHERE post_id=p.id) as comment_count,
                   {liked_sub}
            FROM posts p JOIN users u ON u.id=p.user_id
            ORDER BY like_count DESC, p.created_at DESC LIMIT ? OFFSET ?
        """, (limit, offset))
        return [dict(r) for r in rows]


# ── Likes ─────────────────────────────────────────────────────────────────────

async def toggle_like(user_id, post_id):
    async with await get_db() as db:
        row = await db.execute_fetchone("SELECT 1 FROM likes WHERE user_id=? AND post_id=?", (user_id, post_id))
        if row:
            await db.execute("DELETE FROM likes WHERE user_id=? AND post_id=?", (user_id, post_id))
            await db.commit()
            return False   # unliked
        else:
            await db.execute("INSERT INTO likes VALUES (?,?,?)", (user_id, post_id, time.time()))
            await db.commit()
            return True    # liked


# ── Comments ──────────────────────────────────────────────────────────────────

async def add_comment(post_id, user_id, text):
    async with await get_db() as db:
        cur = await db.execute(
            "INSERT INTO comments (post_id,user_id,text,created_at) VALUES (?,?,?,?)",
            (post_id, user_id, text, time.time()))
        await db.commit()
        return cur.lastrowid


async def get_comments(post_id, limit=50):
    async with await get_db() as db:
        rows = await db.execute_fetchall("""
            SELECT c.*, u.username, u.avatar_url FROM comments c
            JOIN users u ON u.id=c.user_id WHERE c.post_id=?
            ORDER BY c.created_at ASC LIMIT ?
        """, (post_id, limit))
        return [dict(r) for r in rows]


async def delete_comment(comment_id, user_id):
    async with await get_db() as db:
        await db.execute("DELETE FROM comments WHERE id=? AND user_id=?", (comment_id, user_id))
        await db.commit()


# ── Stories ───────────────────────────────────────────────────────────────────

async def create_story(user_id, image_url, caption=""):
    expires = time.time() + 86400  # 24 hours
    async with await get_db() as db:
        cur = await db.execute(
            "INSERT INTO stories (user_id,image_url,caption,expires_at,created_at) VALUES (?,?,?,?,?)",
            (user_id, image_url, caption, expires, time.time()))
        await db.commit()
        return cur.lastrowid


async def get_stories_feed(user_id):
    """Active stories from followed users + own stories, grouped by user."""
    now = time.time()
    async with await get_db() as db:
        rows = await db.execute_fetchall("""
            SELECT s.*, u.username, u.avatar_url,
                   (SELECT COUNT(*) FROM story_views WHERE story_id=s.id AND viewer_id=?) as is_viewed
            FROM stories s JOIN users u ON u.id=s.user_id
            WHERE s.expires_at > ?
              AND (s.user_id IN (SELECT following_id FROM follows WHERE follower_id=?) OR s.user_id=?)
            ORDER BY u.id, s.created_at DESC
        """, (user_id, now, user_id, user_id))
        # Group by user
        grouped, seen = [], set()
        for r in rows:
            rd = dict(r)
            if rd["user_id"] not in seen:
                seen.add(rd["user_id"])
                grouped.append({
                    "user_id": rd["user_id"], "username": rd["username"],
                    "avatar_url": rd["avatar_url"], "has_unseen": not rd["is_viewed"],
                    "stories": []
                })
            grouped[-1]["stories"].append(rd)
        return grouped


async def view_story(story_id, viewer_id):
    async with await get_db() as db:
        try:
            await db.execute("INSERT INTO story_views VALUES (?,?,?)", (story_id, viewer_id, time.time()))
            await db.commit()
        except Exception:
            pass


# ── Notifications ─────────────────────────────────────────────────────────────

async def create_notification(user_id, actor_id, ntype, ref_id=None):
    if user_id == actor_id:
        return
    async with await get_db() as db:
        await db.execute(
            "INSERT INTO notifications (user_id,actor_id,type,ref_id,created_at) VALUES (?,?,?,?,?)",
            (user_id, actor_id, ntype, ref_id, time.time()))
        await db.commit()


async def get_notifications(user_id, limit=30):
    async with await get_db() as db:
        rows = await db.execute_fetchall("""
            SELECT n.*, u.username, u.avatar_url FROM notifications n
            JOIN users u ON u.id=n.actor_id
            WHERE n.user_id=? ORDER BY n.created_at DESC LIMIT ?
        """, (user_id, limit))
        return [dict(r) for r in rows]


async def mark_notifications_read(user_id):
    async with await get_db() as db:
        await db.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))
        await db.commit()


async def unread_count(user_id):
    async with await get_db() as db:
        row = await db.execute_fetchone(
            "SELECT COUNT(*) as c FROM notifications WHERE user_id=? AND is_read=0", (user_id,))
        return row["c"]