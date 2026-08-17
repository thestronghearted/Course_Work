"""Exercise 19 — Documentation Navigation for FastAPI: a small blog API.

Built incrementally from the FastAPI docs' recommended patterns, feature by
feature: user registration, CRUD for blog posts, comments on posts, and basic
search. Uses APIRouter to organise the API (the docs' "Bigger Applications"
guidance) and Pydantic models for validation. Storage is in-memory.

Run:  uvicorn app:app --reload   →  docs at /docs
"""
from datetime import datetime, timezone
from itertools import count
from typing import Optional

from fastapi import APIRouter, FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

app = FastAPI(title="Blog API (Exercise 19)", version="1.0.0")

# --- In-memory stores -------------------------------------------------------
_users: dict[str, "User"] = {}
_posts: dict[int, "Post"] = {}
_comments: dict[int, list["Comment"]] = {}
_post_ids = count(1)
_comment_ids = count(1)


# --- Models -----------------------------------------------------------------
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")


class User(UserCreate):
    pass


class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)
    author: str


class Post(PostCreate):
    id: int
    created_at: datetime


class CommentCreate(BaseModel):
    author: str
    text: str = Field(..., min_length=1, max_length=1000)


class Comment(CommentCreate):
    id: int
    post_id: int


# --- Users router -----------------------------------------------------------
users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate):
    if payload.username in _users:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already taken")
    user = User(**payload.model_dump())
    _users[user.username] = user
    return user


# --- Posts router -----------------------------------------------------------
posts_router = APIRouter(prefix="/posts", tags=["posts"])


def _get_post_or_404(post_id: int) -> "Post":
    post = _posts.get(post_id)
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Post {post_id} not found")
    return post


@posts_router.post("", response_model=Post, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate):
    if payload.author not in _users:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Unknown author")
    post = Post(id=next(_post_ids), created_at=datetime.now(timezone.utc), **payload.model_dump())
    _posts[post.id] = post
    _comments[post.id] = []
    return post


@posts_router.get("", response_model=list[Post])
def list_posts():
    return list(_posts.values())


@posts_router.get("/{post_id}", response_model=Post)
def get_post(post_id: int):
    return _get_post_or_404(post_id)


@posts_router.put("/{post_id}", response_model=Post)
def update_post(post_id: int, payload: PostCreate):
    existing = _get_post_or_404(post_id)
    updated = Post(id=post_id, created_at=existing.created_at, **payload.model_dump())
    _posts[post_id] = updated
    return updated


@posts_router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int):
    _get_post_or_404(post_id)
    del _posts[post_id]
    _comments.pop(post_id, None)


@posts_router.post("/{post_id}/comments", response_model=Comment,
                   status_code=status.HTTP_201_CREATED)
def add_comment(post_id: int, payload: CommentCreate):
    _get_post_or_404(post_id)
    comment = Comment(id=next(_comment_ids), post_id=post_id, **payload.model_dump())
    _comments[post_id].append(comment)
    return comment


@posts_router.get("/{post_id}/comments", response_model=list[Comment])
def list_comments(post_id: int):
    _get_post_or_404(post_id)
    return _comments[post_id]


# --- Search router ----------------------------------------------------------
search_router = APIRouter(tags=["search"])


@search_router.get("/search", response_model=list[Post])
def search_posts(q: str = Query(..., min_length=1, description="Case-insensitive text match")):
    needle = q.lower()
    return [p for p in _posts.values()
            if needle in p.title.lower() or needle in p.body.lower()]


app.include_router(users_router)
app.include_router(posts_router)
app.include_router(search_router)


@app.get("/")
def root():
    return {"message": "Blog API", "docs": "/docs"}
