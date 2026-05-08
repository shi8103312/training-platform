"""
Authentication Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)
    device_info: Optional[str] = Field(None, max_length=255)


class LoginResponse(BaseModel):
    code: int = 0
    data: Optional[dict] = None


class TokenData(BaseModel):
    token: str
    refresh_token: str
    expires_in: int
    user: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class UserInfo(BaseModel):
    user_id: str
    username: str
    real_name: str
    email: str
    role: int
    role_text: str
    dept_id: str
    dept_name: Optional[str] = None
    dept_path: Optional[str] = None
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


class LoginSuccessData(BaseModel):
    token: str
    refresh_token: str
    expires_in: int
    user: UserInfo


class LoginSuccessResponse(BaseModel):
    code: int = 0
    data: LoginSuccessData