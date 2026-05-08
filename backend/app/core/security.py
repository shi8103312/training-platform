"""
JWT Token and Password Security
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import jwt
import secrets
from passlib.context import CryptContext

from ..config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """
    Hash a password.
    """
    return pwd_context.hash(password)


def create_access_token(
    user_id: str,
    role: int,
    dept_id: str,
    expires_delta: Optional[timedelta] = None,
) -> Tuple[str, datetime]:
    """
    Create JWT access token.
    Returns (token, expires_at)
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    payload = {
        "sub": user_id,
        "role": role,
        "dept_id": dept_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": secrets.token_hex(16),
        "type": "access",
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token, expire


def create_refresh_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None,
) -> Tuple[str, datetime]:
    """
    Create JWT refresh token.
    Returns (token, expires_at)
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": secrets.token_hex(16),
        "type": "refresh",
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token, expire


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate JWT token.
    Returns payload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def create_play_token(
    user_id: str,
    material_id: str,
) -> Tuple[str, datetime]:
    """
    Create video play token with 30-second validity.
    Returns (token, expires_at)
    """
    expire = datetime.utcnow() + timedelta(
        seconds=settings.VIDEO_PLAY_TOKEN_VALIDITY_SECONDS
    )

    nonce = secrets.token_hex(8)

    payload = {
        "sub": user_id,
        "material_id": material_id,
        "nonce": nonce,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "play",
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token, expire