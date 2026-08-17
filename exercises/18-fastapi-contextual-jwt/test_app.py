"""Tests for the JWT auth demo (Exercise 18)."""
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def _login(username="johndoe", password="secret"):
    return client.post("/token", data={"username": username, "password": password})


def test_login_success_returns_token():
    r = _login()
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_wrong_password():
    r = _login(password="wrong")
    assert r.status_code == 401


def test_protected_endpoint_requires_token():
    assert client.get("/users/me").status_code == 401


def test_protected_endpoint_with_token():
    token = _login().json()["access_token"]
    r = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "johndoe"


def test_protected_endpoint_rejects_garbage_token():
    r = client.get("/users/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert r.status_code == 401


def test_own_items_scoped_to_user():
    token = _login().json()["access_token"]
    r = client.get("/users/me/items", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()[0]["owner"] == "johndoe"
