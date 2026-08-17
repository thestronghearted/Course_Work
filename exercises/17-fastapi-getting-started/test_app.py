"""Tests for the To-Do API (Exercise 17) using FastAPI's TestClient."""
import pytest
from fastapi.testclient import TestClient

import app as app_module
from app import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_store():
    # Isolate each test: clear the in-memory store and id counter.
    app_module._todos.clear()
    app_module._next_id = 1
    yield


def test_create_todo():
    r = client.post("/todos", json={"title": "Write report", "due_date": "2026-08-15"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1
    assert body["title"] == "Write report"
    assert body["status"] == "pending"


def test_create_rejects_empty_title():
    r = client.post("/todos", json={"title": ""})
    assert r.status_code == 422  # validation error (min_length=1)


def test_list_and_status_filter():
    client.post("/todos", json={"title": "a"})
    client.post("/todos", json={"title": "b"})
    client.patch("/todos/2/complete")

    assert len(client.get("/todos").json()) == 2
    pending = client.get("/todos", params={"status": "pending"}).json()
    assert [t["id"] for t in pending] == [1]
    completed = client.get("/todos", params={"status": "completed"}).json()
    assert [t["id"] for t in completed] == [2]


def test_complete_todo():
    client.post("/todos", json={"title": "x"})
    r = client.patch("/todos/1/complete")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


def test_delete_todo():
    client.post("/todos", json={"title": "x"})
    assert client.delete("/todos/1").status_code == 204
    assert client.get("/todos/1").status_code == 404


def test_404_on_missing():
    assert client.get("/todos/999").status_code == 404
    assert client.patch("/todos/999/complete").status_code == 404
    assert client.delete("/todos/999").status_code == 404
