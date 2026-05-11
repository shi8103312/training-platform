"""
Training Material API Routes
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import os
import aiofiles
import subprocess
import json
from datetime import datetime

from ...database import get_db
from ...models.user import User
from ...models.training import Material, Project
from ...api.deps import get_current_user, require_hr_admin
from ...core.security import create_play_token
from ...config import settings

router = APIRouter(prefix="/training/material", tags=["培训材料"])


ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "wmv"}
ALLOWED_DOCUMENT_EXTENSIONS = {"pdf", "doc", "docx"}


async def get_video_duration(file_path: str) -> int:
    """Extract video duration in seconds using ffprobe."""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            duration = float(data.get("format", {}).get("duration", 0))
            return int(duration)
    except Exception as e:
        print(f"Error extracting video duration: {e}")
    return 0


@router.post("/upload")
async def upload_material(
    project_id: str = Form(...),
    title: str = Form(..., max_length=100),
    material_type: int = Form(..., ge=1, le=2),
    file: UploadFile = File(...),
    sort_order: int = Form(default=0),
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Upload training material (HR admin only).

    material_type: 1=Video, 2=Document
    """
    # Validate project exists
    project = db.query(Project).filter(
        Project.project_id == project_id,
        Project.is_deleted == 0,
    ).first()

    if not project:
        return {
            "code": 20001,
            "message": "项目不存在",
        }

    # Validate file extension
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if material_type == 1:  # Video
        if ext not in ALLOWED_VIDEO_EXTENSIONS:
            return {
                "code": 30005,
                "message": f"不支持的视频格式，仅支持: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}",
            }
    else:  # Document
        if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
            return {
                "code": 30005,
                "message": f"不支持的文档格式，仅支持: {', '.join(ALLOWED_DOCUMENT_EXTENSIONS)}",
            }

    # Read file size
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if material_type == 1 and file_size > settings.MAX_VIDEO_SIZE:
        return {
            "code": 30004,
            "message": "视频文件大小不能超过2GB",
        }
    if material_type == 2 and file_size > settings.MAX_DOCUMENT_SIZE:
        return {
            "code": 30004,
            "message": "文档文件大小不能超过100MB",
        }

    # Generate material ID
    material_id = f"M{uuid.uuid4().hex[:8].upper()}"

    # Generate storage path
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    storage_path = f"materials/{project_id}/{timestamp}_{material_id}.{ext}"

    # TODO: Upload to OSS
    # For now, just save locally for testing
    upload_dir = os.path.join("uploads", "materials", project_id)
    os.makedirs(upload_dir, exist_ok=True)
    local_path = os.path.join(upload_dir, f"{timestamp}_{material_id}.{ext}")

    async with aiofiles.open(local_path, "wb") as f:
        await f.write(content)

    # Get duration for video using ffprobe
    duration = None
    if material_type == 1:
        duration = await get_video_duration(local_path)

    # Generate encryption key for video
    encryption_key = None
    if material_type == 1:
        encryption_key = str(uuid.uuid4()).replace("-", "")[:16]

    # Create material record
    material = Material(
        material_id=material_id,
        project_id=project_id,
        title=title,
        material_type=material_type,
        storage_path=storage_path,
        file_size=file_size,
        file_extension=ext,
        mime_type=_get_mime_type(ext),
        duration=duration,
        encryption_key=encryption_key,
        sort_order=sort_order,
    )

    db.add(material)
    db.commit()
    db.refresh(material)

    return {
        "code": 0,
        "data": {
            "material_id": material.material_id,
            "title": material.title,
            "material_type": material.material_type,
            "duration": material.duration,
            "file_size": material.file_size,
            "status": "processing" if material_type == 1 else "ready",
        },
    }


def _get_mime_type(ext: str) -> str:
    """Get MIME type from extension."""
    mime_types = {
        "mp4": "video/mp4",
        "avi": "video/x-msvideo",
        "mov": "video/quicktime",
        "wmv": "video/x-ms-wmv",
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    return mime_types.get(ext.lower(), "application/octet-stream")


@router.get("/{material_id}/play-token")
async def get_play_token(
    material_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get video play token for secure playback.
    Token validity: 30 seconds.
    """
    # Get material
    material = db.query(Material).filter(
        Material.material_id == material_id,
        Material.is_deleted == 0,
    ).first()

    if not material:
        return {
            "code": 30001,
            "message": "材料不存在",
        }

    if not material.is_video:
        return {
            "code": 30003,
            "message": "该材料不是视频",
        }

    # Check project is published
    project = material.project
    if project.status != 1:
        return {
            "code": 20005,
            "message": "项目未发布",
        }

    # Generate play token
    token, expires_at = create_play_token(
        user_id=current_user.user_id,
        material_id=material_id,
    )

    return {
        "code": 0,
        "data": {
            "play_url": material.storage_path,  # This is the storage path, will be prefixed with /uploads/ on frontend
            "token": token,
            "token_expires_at": expires_at.isoformat(),
        },
    }


@router.put("/{material_id}/duration")
async def update_material_duration(
    material_id: str,
    duration: int = Query(..., ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update video material duration.
    Called when video metadata is loaded to save actual duration.
    """
    material = db.query(Material).filter(
        Material.material_id == material_id,
        Material.is_deleted == 0,
    ).first()

    if not material:
        return {
            "code": 30001,
            "message": "材料不存在",
        }

    # Only update if current duration is 0 or smaller
    if material.duration is None or material.duration == 0 or duration < material.duration:
        material.duration = duration
        db.commit()
        print(f"[DEBUG] Updated material {material_id} duration to {duration}")

    return {
        "code": 0,
        "message": "时长已更新",
    }


@router.delete("/{material_id}")
async def delete_material(
    material_id: str,
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Delete training material (HR admin only).
    Soft delete - original file cleaned up after 30 days.
    """
    material = db.query(Material).filter(
        Material.material_id == material_id,
        Material.is_deleted == 0,
    ).first()

    if not material:
        return {
            "code": 30001,
            "message": "材料不存在",
        }

    # Soft delete
    material.is_deleted = 1
    db.commit()

    return {
        "code": 0,
        "message": "删除成功",
    }