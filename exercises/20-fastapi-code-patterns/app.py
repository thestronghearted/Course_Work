"""Exercise 20 — Understanding FastAPI Code Patterns.

A runnable, in-memory adaptation of the course's advanced sample. It keeps the
same patterns the exercise asks you to understand — a generic Repository, layered
dependency injection, timing middleware, JWT auth, role-based access control, and
a lifespan handler — and adds the Part 4 feature: an action log that records user
logins and admin actions, using the SAME patterns (a repository + service).

The original used SQLAlchemy async; here the "database" is an in-memory store so
the file runs without external services while preserving the architecture.

Run:  uvicorn app:app --reload
"""
from datetime import datetime, timedelta, timezone
from typing import Generic, Optional, TypeVar
import hashlib

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

SECRET_KEY = "dev-secret"
ALGORITHM = "HS256"

# --- Domain models ----------------------------------------------------------
class User(BaseModel):
    id: int
    username: str
    hashed_password: str
    is_superuser: bool = False
    disabled: bool = False


class ActionLog(BaseModel):
    id: int
    username: str
    action: str
    at: datetime


# --- Generic Repository pattern ---------------------------------------------
T = TypeVar("T", bound=BaseModel)


class Repository(Generic[T]):
    """In-memory generic repository keyed by integer id."""

    def __init__(self):
        self._items: dict[int, T] = {}
        self._seq = 0

    def add(self, item: T) -> T:
        self._items[item.id] = item
        self._seq = max(self._seq, item.id)
        return item

    def next_id(self) -> int:
        self._seq += 1
        return self._seq

    def get(self, item_id: int) -> Optional[T]:
        return self._items.get(item_id)

    def list(self, skip: int = 0, limit: int = 100) -> list[T]:
        return list(self._items.values())[skip: skip + limit]


class UserRepository(Repository[User]):
    def get_by_username(self, username: str) -> Optional[User]:
        return next((u for u in self._items.values() if u.username == username), None)


# --- "Database" (single in-memory instance) + DI dependency -----------------
class Database:
    def __init__(self):
        self.users = UserRepository()
        self.logs = Repository[ActionLog]()


_db = Database()


def get_db() -> Database:
    # Dependency: in the original this yielded a DB session; here it hands out
    # the in-memory store. Kept as a dependency so it's injectable/overridable.
    return _db


# --- Password + token helpers ----------------------------------------------
def _hash(pw: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), b"salt", 100_000).hex()


def create_access_token(username: str) -> str:
    payload = {"sub": username, "exp": datetime.now(timezone.utc) + timedelta(minutes=30)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# --- Service layer ----------------------------------------------------------
class UserService:
    def __init__(self, db: Database):
        self.db = db

    def authenticate(self, username: str, password: str) -> Optional[User]:
        user = self.db.users.get_by_username(username)
        if not user or user.hashed_password != _hash(password):
            return None
        return user


class ActionLogService:
    """Part 4 feature — records user actions using the repository pattern."""

    def __init__(self, db: Database):
        self.db = db

    def record(self, username: str, action: str) -> ActionLog:
        entry = ActionLog(id=self.db.logs.next_id(), username=username,
                          action=action, at=datetime.now(timezone.utc))
        return self.db.logs.add(entry)

    def all(self) -> list[ActionLog]:
        return self.db.logs.list()


# --- Auth dependencies ------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme),
                           db: Database = Depends(get_db)) -> User:
    creds_exc = HTTPException(status.HTTP_401_UNAUTHORIZED,
                             detail="Invalid credentials",
                             headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise creds_exc
    except jwt.PyJWTError:
        raise creds_exc
    user = db.users.get_by_username(username)
    if user is None:
        raise creds_exc
    return user


def require_role(role: str):
    """Dependency factory for role-based access control.

    The original sample used a decorator; a dependency is the idiomatic FastAPI
    equivalent — composable, testable, and visible in the OpenAPI schema.
    """
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if role == "admin" and not current_user.is_superuser:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return checker


# --- App + lifespan + middleware -------------------------------------------
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: seed users.
    _db.users.add(User(id=_db.users.next_id(), username="admin",
                       hashed_password=_hash("admin"), is_superuser=True))
    _db.users.add(User(id=_db.users.next_id(), username="johndoe",
                       hashed_password=_hash("secret")))
    yield
    # Shutdown: nothing to clean up for the in-memory store.


app = FastAPI(title="FastAPI Patterns Demo (Exercise 20)", lifespan=lifespan)


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start = datetime.now(timezone.utc)
    response = await call_next(request)
    elapsed_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
    response.headers["X-Process-Time"] = f"{elapsed_ms:.2f}"
    return response


# --- Schemas / endpoints ----------------------------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str


class UserOut(BaseModel):
    id: int
    username: str
    is_superuser: bool


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(),
                db: Database = Depends(get_db)):
    user = UserService(db).authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    ActionLogService(db).record(user.username, "login")  # Part 4: log the login
    return {"access_token": create_access_token(user.username), "token_type": "bearer"}


@app.get("/users/me", response_model=UserOut)
async def read_me(current_user: User = Depends(get_current_user)):
    return UserOut(**current_user.model_dump())


@app.get("/admin/users", response_model=list[UserOut])
async def list_users(current_user: User = Depends(require_role("admin")),
                     db: Database = Depends(get_db), skip: int = 0, limit: int = 10):
    ActionLogService(db).record(current_user.username, "list_users")  # Part 4: log admin action
    return [UserOut(**u.model_dump()) for u in db.users.list(skip, limit)]


@app.get("/admin/logs", response_model=list[ActionLog])
async def list_logs(current_user: User = Depends(require_role("admin")),
                    db: Database = Depends(get_db)):
    return ActionLogService(db).all()
