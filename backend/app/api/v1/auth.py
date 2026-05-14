"""
Authentication API Routes
"""
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer
from datetime import datetime, timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address
import uuid
import secrets
import string

from ...database import get_db
from ...core.security import (
    verify_password,
    hash_password,
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
from ...models.user import User, AuthToken, PasswordResetToken
from ...redis import redis_client
from ...config import settings
from ...schemas.auth import (
    LoginRequest,
    LoginSuccessResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)

router = APIRouter(prefix="/auth", tags=["认证"])

# Rate limiter for auth endpoints
auth_limiter = Limiter(key_func=get_remote_address)


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
@auth_limiter.limit("5/minute")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    User login endpoint.
    Rate limited to 5 attempts per minute per IP.
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
    # Use longer expiry if "remember me" is checked
    expire_minutes = (
        settings.ACCESS_TOKEN_EXPIRE_MINUTES_REMEMBER
        if login_data.remember_me
        else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    access_token, access_expires = create_access_token(
        user_id=user.user_id,
        role=user.role,
        dept_id=user.dept_id,
        expires_delta=timedelta(minutes=expire_minutes),
    )

    refresh_token, refresh_expires = create_refresh_token(user_id=user.user_id)

    # Generate token_id early for Remember Me tracking
    token_id = str(uuid.uuid4())

    # If "Remember Me" is checked, invalidate any previous Remember Me token for this IP
    client_ip = request.client.host if request.client else None
    if login_data.remember_me and client_ip:
        previous_remember_key = f"remember_me:{client_ip}"
        previous_token_id = redis_client.get(previous_remember_key)
        if previous_token_id:
            # Invalidate the previous Remember Me token by setting short expiry
            old_token = db.query(AuthToken).filter(
                AuthToken.token_id == (
                    previous_token_id.decode() if isinstance(previous_token_id, bytes)
                    else previous_token_id
                )
            ).first()
            if old_token:
                old_token.expires_at = datetime.utcnow() + timedelta(minutes=5)  # Shorten to 5 minutes
                db.commit()
        # Store new Remember Me mapping
        redis_client.setex(previous_remember_key, expire_minutes * 60, token_id)

    # Store token in database
    auth_token = AuthToken(
        token_id=token_id,
        user_id=user.user_id,
        token=access_token,
        refresh_token=refresh_token,
        device_info=login_data.device_info,
        ip_address=client_ip,
        expires_at=access_expires,
    )
    db.add(auth_token)
    db.commit()

    return LoginSuccessResponse(
        code=0,
        data={
            "token": access_token,
            "refresh_token": refresh_token,
            "expires_in": expire_minutes * 60,
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "real_name": user.real_name,
                "email": user.email,
                "role": user.role,
                "role_text": "超级管理员" if user.role == Role.SUPER_ADMIN else "HR管理员" if user.role == Role.HR_ADMIN else "员工",
                "dept_id": user.dept_id,
                "avatar": user.avatar,
                "preferences": user.preferences or {},
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


@router.post("/forgot-password")
@auth_limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    forgot_data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Request password reset.
    Generates a reset token sent via email (or displayed for demo).
    Rate limited to 3 attempts per minute per IP.
    """
    username = forgot_data.username

    # Check if account is locked
    if _check_login_locked(username):
        raise_account_locked_error()

    # Get user by username
    user = db.query(User).filter(User.username == username).first()

    if not user:
        # Don't reveal if user exists or not
        return {
            "code": 0,
            "message": "如果用户名存在，重置链接已发送",
        }

    # Check if user is active
    if user.status != 1:
        return {
            "code": 0,
            "message": "如果用户名存在，重置链接已发送",
        }

    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    token_id = str(uuid.uuid4())

    # Delete any existing reset tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.user_id
    ).delete()

    # Create new reset token (expires in 1 hour)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    password_reset = PasswordResetToken(
        token_id=token_id,
        user_id=user.user_id,
        token=reset_token,
        expires_at=expires_at,
    )
    db.add(password_reset)
    db.commit()

    # Check if SMTP is configured
    if settings.SMTP_HOST and settings.SMTP_USER:
        # TODO: Send actual email with reset link
        # For now, just log and return success
        reset_link = f"http://localhost:5173/reset-password?token={reset_token}"
        print(f"Password reset link for {username}: {reset_link}")
        return {
            "code": 0,
            "message": "重置链接已发送到您的邮箱",
        }
    else:
        # For demo: return token directly (in production, this should be sent via email)
        reset_link = f"http://localhost:5173/reset-password?token={reset_token}"
        print(f"Password reset link (demo): {reset_link}")
        return {
            "code": 0,
            "message": "演示模式：重置链接如下（生产环境会发送至邮箱）",
            "data": {
                "reset_token": reset_token,
                "reset_link": reset_link,
            },
        }


@router.post("/reset-password")
@auth_limiter.limit("5/minute")
async def reset_password(
    request: Request,
    reset_data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Reset password using token.
    Rate limited to 5 attempts per minute per IP.
    """
    # Find valid reset token
    password_reset = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == reset_data.reset_token,
        PasswordResetToken.used == 0,
        PasswordResetToken.expires_at > datetime.utcnow(),
    ).first()

    if not password_reset:
        return {
            "code": 40001,
            "message": "重置链接无效或已过期",
        }

    # Get user
    user = db.query(User).filter(
        User.user_id == password_reset.user_id,
        User.status == 1,
    ).first()

    if not user:
        return {
            "code": 40001,
            "message": "重置链接无效或已过期",
        }

    # Hash new password
    new_password_hash = hash_password(reset_data.new_password)

    # Update user password
    user.password_hash = new_password_hash

    # Mark token as used
    password_reset.used = 1

    # Clear any failed login attempts
    _clear_failed_attempts(user.username)

    db.commit()

    return {
        "code": 0,
        "message": "密码重置成功，请使用新密码登录",
    }