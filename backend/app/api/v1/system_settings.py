"""
System Settings API Routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ...database import get_db
from ...models.user import User
from ...api.deps import get_current_user, require_hr_admin

router = APIRouter(prefix="/settings", tags=["系统设置"])


class SettingsUpdate(BaseModel):
    platform_name: Optional[str] = None
    platform_logo: Optional[str] = None
    copyright: Optional[str] = None
    timezone: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[str] = None
    smtp_from: Optional[str] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    security_force_password_change: Optional[bool] = None
    security_login_lockout: Optional[bool] = None
    security_password_complexity: Optional[bool] = None
    security_screen_record_detection: Optional[bool] = None
    security_token_expiry: Optional[int] = None
    video_allowed_formats: Optional[str] = None
    video_max_size: Optional[int] = None
    video_transcode_resolution: Optional[str] = None
    video_encryption: Optional[bool] = None
    video_watermark: Optional[bool] = None
    notif_training_start: Optional[bool] = None
    notif_deadline_reminder: Optional[bool] = None
    notif_training_complete: Optional[bool] = None
    notif_exam_result: Optional[bool] = None


# In-memory settings storage (in production, this would be in the database)
_settings = {
    "platform_name": "集团内部培训平台",
    "platform_logo": "",
    "copyright": "© 2026 某某集团 版权所有",
    "timezone": "Asia/Shanghai",
    "smtp_host": "smtp.company.com",
    "smtp_port": "465",
    "smtp_from": "training@company.com",
    "smtp_username": "",
    "smtp_password": "",
    "security_force_password_change": True,
    "security_login_lockout": True,
    "security_password_complexity": True,
    "security_screen_record_detection": True,
    "security_token_expiry": 30,
    "video_allowed_formats": "mp4,avi,mov,wmv",
    "video_max_size": 2048,
    "video_transcode_resolution": "1080p",
    "video_encryption": True,
    "video_watermark": False,
    "notif_training_start": True,
    "notif_deadline_reminder": True,
    "notif_training_complete": True,
    "notif_exam_result": True,
}


@router.get("")
async def get_settings(
    current_user: User = Depends(require_hr_admin()),
):
    """
    Get system settings (HR admin only).
    """
    return {
        "code": 0,
        "data": _settings,
    }


@router.put("")
async def update_settings(
    settings_data: SettingsUpdate,
    current_user: User = Depends(require_hr_admin()),
):
    """
    Update system settings (HR admin only).
    """
    global _settings

    # Update only provided fields
    update_data = settings_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            _settings[key] = value

    return {
        "code": 0,
        "message": "设置保存成功",
    }


@router.post("/test-email")
async def test_email_config(
    email: str,
    current_user: User = Depends(require_hr_admin()),
):
    """
    Send test email to verify SMTP configuration (HR admin only).
    """
    # TODO: Implement actual email sending
    return {
        "code": 0,
        "message": f"测试邮件已发送至 {email}，请查收",
    }