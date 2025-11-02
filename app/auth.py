"""Authentication helpers and FastAPI dependencies."""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status

from .schemas import AuthenticatedUser, Role
from .storage import InMemoryDatabase, get_db


def get_token(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return authorization.split(" ", 1)[1]


def get_current_user(token: str = Depends(get_token), db: InMemoryDatabase = Depends(get_db)) -> AuthenticatedUser:
    user = db.user_from_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_TOKEN")
    return AuthenticatedUser.parse_obj(user.dict(by_alias=True))


def get_admin_user(current: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    if current.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    return current
