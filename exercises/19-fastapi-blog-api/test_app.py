"""Tests for the Blog API (Exercise 19)."""
import pytest
from fastapi.testclient import TestClient

import app as app_module
from app import app
from itertools import count

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    app_module._users.clear()
    app_module._posts.clear()
    app_module._comments.clear()
    app_module._post_ids = count(1)
    app_module._comment_ids = count(1)
    yield


def _register(username="alice", email="alice@example.com"):
    return client.post("/users", json={"username": username, "email": email})


def _create_post(author="alice", title="Hello", body="World body"):
    return client.post("/posts", json={"title": title, "body": body, "author": author})


def test_register_user_and_conflict():
    assert _register().status_code == 201
    assert _register().status_code == 409  # duplicate username


def test_register_rejects_bad_email():
    r = client.post("/users", json={"username": "bob", "email": "not-an-email"})
    assert r.status_code == 422


def test_create_post_requires_known_author():
    assert _create_post(author="ghost").status_code == 400
    _register()
    assert _create_post().status_code == 201


def test_post_crud():
    _register()
    pid = _create_post().json()["id"]
    assert client.get(f"/posts/{pid}").status_code == 200
    r = client.put(f"/posts/{pid}", json={"title": "Edited", "body": "New body", "author": "alice"})
    assert r.json()["title"] == "Edited"
    assert client.delete(f"/posts/{pid}").status_code == 204
    assert client.get(f"/posts/{pid}").status_code == 404


def test_comments():
    _register()
    pid = _create_post().json()["id"]
    r = client.post(f"/posts/{pid}/comments", json={"author": "alice", "text": "Nice!"})
    assert r.status_code == 201
    comments = client.get(f"/posts/{pid}/comments").json()
    assert [c["text"] for c in comments] == ["Nice!"]


def test_comment_on_missing_post_404():
    assert client.post("/posts/999/comments", json={"author": "x", "text": "y"}).status_code == 404


def test_search():
    _register()
    _create_post(title="Python tips", body="about generators")
    _create_post(title="Go basics", body="about goroutines")
    hits = client.get("/search", params={"q": "python"}).json()
    assert [p["title"] for p in hits] == ["Python tips"]
    body_hits = client.get("/search", params={"q": "goroutines"}).json()
    assert [p["title"] for p in body_hits] == ["Go basics"]
