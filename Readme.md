# Photogram — Instagram Clone
A full-stack Instagram-style social media app built with FastAPI + vanilla HTML/CSS/JS.

---

## Features

- 📸 **Photo Posts** — upload images with captions and hashtags
- 🎬 **Stories** — 24-hour disappearing stories with image support
- ❤️ **Likes & Comments** — engage with posts
- 👥 **Follow System** — follow/unfollow users, follower/following counts
- 🏠 **Feed** — posts from people you follow, newest first
- 🔍 **Explore** — discover posts & users
- 🔔 **Notifications** — likes, comments, follows
- 👤 **Profiles** — avatar, bio, post grid
- 🔐 **Auth** — JWT-based register/login

---

## Project Structure

```
photogram/
├── main.py                        # FastAPI entry point
├── requirements.txt
├── README.md
├── backend/
│   ├── api/
│   │   ├── auth.py                # Register, login, JWT
│   │   ├── posts.py               # CRUD posts, likes, comments
│   │   ├── stories.py             # Stories (24h TTL)
│   │   ├── users.py               # Profiles, follow/unfollow
│   │   ├── feed.py                # Home feed & explore
│   │   └── notifications.py       # Notification endpoints
│   ├── db/
│   │   └── database.py            # SQLite schema + queries
│   ├── models/
│   │   └── schemas.py             # Pydantic schemas
│   └── utils/
│       ├── auth.py                # JWT helpers, password hashing
│       └── images.py              # Image upload & validation
├── frontend/
│   ├── templates/index.html       # SPA shell
│   └── static/
│       ├── css/style.css
│       └── js/
│           ├── app.js             # Router & bootstrap
│           ├── api.js             # API client
│           ├── auth.js            # Login/register views
│           ├── feed.js            # Home feed
│           ├── explore.js         # Explore page
│           ├── profile.js         # User profile
│           ├── stories.js         # Stories bar + viewer
│           └── post.js            # Single post view
├── uploads/                       # Uploaded media (gitignored)
└── tests/
    └── test_app.py
```

---

## Quick Start

```bash
pip install -r requirements.txt
python main.py
# Open http://localhost:8000
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login → JWT |
| GET  | `/api/users/{username}` | Get profile |
| POST | `/api/users/{username}/follow` | Follow user |
| GET  | `/api/feed` | Home feed |
| GET  | `/api/explore` | Explore posts |
| POST | `/api/posts` | Create post |
| GET  | `/api/posts/{id}` | Get post |
| POST | `/api/posts/{id}/like` | Like/unlike |
| POST | `/api/posts/{id}/comments` | Add comment |
| POST | `/api/stories` | Create story |
| GET  | `/api/stories/feed` | Stories from followed |
| GET  | `/api/notifications` | Get notifications |