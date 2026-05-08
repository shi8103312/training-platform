"""
API Dependencies - Authentication and Authorization
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..core.security import decode_token
from ..core.exceptions import (
    raise_token_expired_error,
    raise_token_invalid_error,
    raise_permission_denied_error,
)
from ..models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token.
    """
    token = credentials.credentials

    # Decode token
    payload = decode_token(token)
    if payload is None:
        raise_token_invalid_error()

    # Check token type
    if payload.get("type") != "access":
        raise_token_invalid_error()

    # Get user from database
    user_id = payload.get("sub")
    if not user_id:
        raise_token_invalid_error()

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise_token_invalid_error()

    # Check if user is active
    if user.status != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_role(*roles: int):
    """
    Dependency factory for role-based access control.

    Usage:
        @router.post("/admin")
        async def admin_endpoint(
            current_user: User = Depends(require_role(Role.HR_ADMIN))
        ):
            ...
    """

    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in roles:
            raise_permission_denied_error()
        return current_user

    return role_checker


def require_hr_admin():
    """
    Dependency that requires HR_ADMIN role.
    """
    return require_role(1)