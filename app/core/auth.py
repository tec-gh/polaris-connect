import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import settings

security = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    expected_username = settings.admin_username.encode("utf-8")
    expected_password = settings.admin_password.encode("utf-8")
    current_username = credentials.username.encode("utf-8")
    current_password = credentials.password.encode("utf-8")
    if not (
        secrets.compare_digest(current_username, expected_username)
        and secrets.compare_digest(current_password, expected_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def verify_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    if not settings.api_key:
        return
    if not x_api_key or not secrets.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
