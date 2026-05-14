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
    remember_me: bool = Field(default=False, description="记住登录状态")


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


class ForgotPasswordRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)


class ResetPasswordRequest(BaseModel):
    reset_token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=50)


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
    preferences: Optional[dict] = None

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


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=50)
    real_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    dept_id: Optional[str] = Field(None, max_length=32)
    role: int = Field(default=2, ge=1, le=2)  # 1=HR_ADMIN, 2=EMPLOYEE
    status: int = Field(default=1, ge=0, le=1)


class UserUpdate(BaseModel):
    real_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    dept_id: Optional[str] = Field(None, max_length=32)
    role: Optional[int] = Field(None, ge=1, le=2)
    status: Optional[int] = Field(None, ge=0, le=1)
    password: Optional[str] = Field(None, min_length=6, max_length=50)


class UserPreferencesUpdate(BaseModel):
    theme: Optional[str] = Field(None, description="Theme: default, sky, forest, sunset, berry")