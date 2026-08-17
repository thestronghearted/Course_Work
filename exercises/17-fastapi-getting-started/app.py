"""Exercise 17 — Getting Started with FastAPI.

A small to-do list REST API demonstrating FastAPI fundamentals:
Pydantic request/response models with validation, path/query parameters,
proper status codes, and error handling. Storage is an in-memory dict (no DB),
which is enough for the exercise.

Run:  uvicorn app:app --reload      →  interactive docs at /docs
"""
from datetime import date
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="To-Do API",
    description="A simple to-do list API built with FastAPI (Exercise 17).",
    version="1.0.0",
)


class TodoStatus(str, Enum):
    pending = "pending"
    completed = "completed"


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Short title")
    description: str = Field("", max_length=2000)
    due_date: Optional[date] = Field(None, description="Optional due date (YYYY-MM-DD)")


class Todo(TodoCreate):
    id: int
    status: TodoStatus = TodoStatus.pending


# In-memory store (id -> Todo). Reset on restart.
_todos: dict[int, Todo] = {}
_next_id = 1


def _get_or_404(todo_id: int) -> Todo:
    todo = _todos.get(todo_id)
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Todo {todo_id} not found")
    return todo


@app.get("/")
def root():
    return {"message": "To-Do API", "docs": "/docs"}


@app.post("/todos", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(payload: TodoCreate):
    """Create a new to-do item."""
    global _next_id
    todo = Todo(id=_next_id, **payload.model_dump())
    _todos[_next_id] = todo
    _next_id += 1
    return todo


@app.get("/todos", response_model=list[Todo])
def list_todos(status_filter: Optional[TodoStatus] = Query(None, alias="status")):
    """List all to-dos, optionally filtered by status (pending/completed)."""
    items = list(_todos.values())
    if status_filter is not None:
        items = [t for t in items if t.status == status_filter]
    return items


@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int):
    return _get_or_404(todo_id)


@app.patch("/todos/{todo_id}/complete", response_model=Todo)
def complete_todo(todo_id: int):
    """Mark a to-do as completed."""
    todo = _get_or_404(todo_id)
    todo.status = TodoStatus.completed
    return todo


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int):
    _get_or_404(todo_id)
    del _todos[todo_id]
    return None
