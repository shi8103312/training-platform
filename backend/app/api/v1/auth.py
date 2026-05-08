"""
Authentication API Routes
"""
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer
from datetime import datetime, timedelta
import uuid

from ...database import get_db
from ...core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from ...core.exceptions import (
    raise_auth_error,
    raise_account_locked_error,
    raise_token_invalid_error,
    raise_token_expired_error,
)
from ...core.permissions import Role
from ...models.user import User, AuthToken
from ...redis import redis_client
from ...config import settings
from ...schemas.auth import (
    LoginRequest,
    LoginSuccessResponse,
    RefreshTokenRequest,
)

router = APIRouter(prefix="/auth", tags=["认证"])


def _check_login_locked(username: str) -> bool:
    """Check if account is locked due to failed login attempts."""
    lock_key = f"login_lock:{username}"
    return redis_client.exists(lock_key)


def _lock_account(username: str):
    """Lock account for 15 minutes."""
    lock_key = f"login_lock:{username}"
    redis_client.setex(lock_key, settings.LOGIN_LOCKOUT_DURATION_MINUTES * 60, "1")


def _increment_failed_attempts(username: str) -> int:
    """Increment failed login attempts and lock if threshold reached."""
    failed_key = f"login_failed:{username}"
    failed_count = redis_client.incr(failed_key)

    if failed_count == 1:
        redis_client.expire(failed_key, settings.LOGIN_LOCKOUT_DURATION_MINUTES * 60)

    if failed_count >= settings.LOGIN_MAX_FAILED_ATTEMPTS:
        _lock_account(username)
        return -1

    return failed_count


def _clear_failed_attempts(username: str):
    """Clear failed login attempts on successful login."""
    failed_key = f"login_failed:{username}"
    redis_client.delete(failed_key)


async def get_current_user_from_request(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    Get current user from request (for logout endpoint).
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证token",
        )

    token = auth_header.split(" ")[1]

    # Decode token
    payload = decode_token(token)
    if payload is None:
        raise_token_expired_error()

    if payload.get("type") != "access":
        raise_token_invalid_error()

    user_id = payload.get("sub")
    if not user_id:
        raise_token_invalid_error()

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    if user.status != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    return user


@router.post("/login", response_model=LoginSuccessResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    User login endpoint.
    """
    username = login_data.username

    # Check if account is locked
    if _check_login_locked(username):
        raise_account_locked_error()

    # Get user from database
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise_auth_error("用户名或密码错误")

    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        failed_count = _increment_failed_attempts(username)
        if failed_count == -1:
            raise_account_locked_error()
        raise_auth_error(f"用户名或密码错误，剩余尝试次数 {settings.LOGIN_MAX_FAILED_ATTEMPTS - failed_count}")

    # Check if user is active
    if user.status != 1:
        raise_auth_error("用户已被禁用")

    # Clear failed attempts
    _clear_failed_attempts(username)

    # Update last login info
    user.last_login_time = datetime.now()
    user.last_login_ip = request.client.host if request.client else None
    db.commit()

    # Generate tokens
    access_token, access_expires = create_access_token(
        user_id=user.user_id,
        role=user.role,
        dept_id=user.dept_id,
    )

    refresh_token, refresh_expires = create_refresh_token(user_id=user.user_id)

    # Store token in database
    token_id = str(uuid.uuid4())
    auth_token = AuthToken(
        token_id=token_id,
        user_id=user.user_id,
        token=access_token,
        refresh_token=refresh_token,
        device_info=login_data.device_info,
        ip_address=request.client.host if request.client else None,
        expires_at=access_expires,
    )
    db.add(auth_token)
    db.commit()

    return LoginSuccessResponse(
        code=0,
        data={
            "token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "real_name": user.real_name,
                "email": user.email,
                "role": user.role,
                "role_text": "HR管理员" if user.role == Role.HR_ADMIN else "员工",
                "dept_id": user.dept_id,
            },
        },
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user_from_request),
    db: Session = Depends(get_db),
):
    """
    User logout endpoint.
    """
    # Delete all tokens for this user
    db.query(AuthToken).filter(AuthToken.user_id == current_user.user_id).delete()
    db.commit()

    return {"code": 0, "message": "登出成功"}


@router.post("/refresh")
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    """
    # Decode refresh token
    payload = decode_token(token_data.refresh_token)
    if payload is None:
        raise_token_invalid_error()

    if payload.get("type") != "refresh":
        raise_token_invalid_error()

    user_id = payload.get("sub")

    # Get user
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or user.status != 1:
        raise_auth_error("用户无效或已禁用")

    # Generate new access token
    access_token, access_expires = create_access_token(
        user_id=user.user_id,
        role=user.role,
        dept_id=user.dept_id,
    )

    return {
        "code": 0,
        "data": {
            "token": access_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        },
    }