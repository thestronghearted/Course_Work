"""Tests for the patterns demo (Exercise 20), including the Part 4 logging feature."""
from fastapi.testclient import TestClient

from app import app


def _client():
    # Context-managed client triggers lifespan (seeds users).
    return TestClient(app)


def _token(client, username, password):
    r = client.post("/token", data={"username": username, "password": password})
    return r.json().get("access_token")


def test_timing_middleware_header_present():
    with _client() as client:
        r = client.get("/")
        # Root isn't defined -> 404, but middleware still runs and sets the header.
        assert "x-process-time" in {k.lower() for k in r.headers}


def test_login_and_me():
    with _client() as client:
        token = _token(client, "johndoe", "secret")
        assert token
        r = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["username"] == "johndoe"


def test_non_admin_forbidden_from_admin_route():
    with _client() as client:
        token = _token(client, "johndoe", "secret")
        r = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403


def test_admin_can_list_users():
    with _client() as client:
        token = _token(client, "admin", "admin")
        r = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        usernames = {u["username"] for u in r.json()}
        assert {"admin", "johndoe"} <= usernames


def test_action_log_records_login_and_admin_action():
    with _client() as client:
        admin = _token(client, "admin", "admin")            # logs a 'login'
        client.get("/admin/users", headers={"Authorization": f"Bearer {admin}"})  # logs 'list_users'
        logs = client.get("/admin/logs", headers={"Authorization": f"Bearer {admin}"}).json()
        actions = [(l["username"], l["action"]) for l in logs]
        assert ("admin", "login") in actions
        assert ("admin", "list_users") in actions


def test_unauthenticated_rejected():
    with _client() as client:
        assert client.get("/users/me").status_code == 401
        assert client.get("/admin/users").status_code == 401
