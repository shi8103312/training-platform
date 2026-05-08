"""
Learning Progress API Routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from datetime import datetime
import uuid

from ...database import get_db
from ...models.user import User
from ...models.training import Project, Material, WatchProgress, Progress
from ...models.exam import Exam, ExamAttempt
from ...api.deps import get_current_user, require_hr_admin
from ...core.permissions import Role
from ...schemas.training import UpdateProgressRequest

router = APIRouter(prefix="/training/progress", tags=["学习进度"])


@router.get("/{project_id}")
async def get_project_progress(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get learning progress for a project.
    Returns material progress and exam status.
    """
    # Get project
    project = db.query(Project).filter(
        Project.project_id == project_id,
        Project.is_deleted == 0,
    ).first()

    if not project:
        return {
            "code": 20001,
            "message": "项目不存在",
        }

    # Get materials
    materials = db.query(Material).filter(
        Material.project_id == project_id,
        Material.is_deleted == 0,
    ).order_by(Material.sort_order).all()

    # Get progress records
    progress_list = db.query(WatchProgress).filter(
        WatchProgress.user_id == current_user.user_id,
        WatchProgress.material_id.in_([m.material_id for m in materials]),
    ).all()

    # Build progress map
    progress_map = {p.material_id: p for p in progress_list}

    # Calculate overall status
    overall_status = 0  # Not started
    completed_count = 0

    material_progress_list = []
    for m in materials:
        progress = progress_map.get(m.material_id)
        if progress:
            is_completed = bool(progress.is_completed)
            progress_pct = progress.progress_percentage
            if is_completed:
                completed_count += 1
                overall_status = 1  # In progress
            material_progress_list.append({
                "material_id": m.material_id,
                "title": m.title,
                "material_type": m.material_type,
                "progress": progress_pct,
                "max_position": progress.max_position,
                "is_completed": is_completed,
                "is_required": True,  # TODO: Add required flag to material
            })
        else:
            material_progress_list.append({
                "material_id": m.material_id,
                "title": m.title,
                "material_type": m.material_type,
                "progress": 0,
                "max_position": 0,
                "is_completed": False,
                "is_required": True,
            })

    # Check if all completed
    if completed_count == len(materials) and len(materials) > 0:
        overall_status = 2  # Completed

    # Get exam status
    exam_status = None
    exam = db.query(Exam).filter(
        Exam.project_id == project_id,
        Exam.is_deleted == 0,
    ).first()

    if exam:
        # Get latest attempt
        attempt = db.query(ExamAttempt).filter(
            ExamAttempt.exam_id == exam.exam_id,
            ExamAttempt.user_id == current_user.user_id,
        ).order_by(ExamAttempt.start_time.desc()).first()

        if attempt:
            exam_status = {
                "exam_id": exam.exam_id,
                "attempt_id": attempt.attempt_id,
                "status": attempt.status_text,
                "score": attempt.score,
            }
        else:
            exam_status = {
                "exam_id": exam.exam_id,
                "attempt_id": None,
                "status": "not_started",
                "score": None,
            }

    return {
        "code": 0,
        "data": {
            "project_id": project_id,
            "overall_status": overall_status,
            "overall_status_text": ["未开始", "进行中", "已完成"][overall_status],
            "materials": material_progress_list,
            "exam": exam_status,
        },
    }


@router.post("/update")
async def update_progress(
    progress_data: UpdateProgressRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update video watching progress.

    Anti-cheating rules:
    - play_position must be >= current max_position
    - If reported position > max_position + 30s, it's considered cheating and ignored
    - Completion: max_position >= total_duration * 95%
    """
    # Get material
    material = db.query(Material).filter(
        Material.material_id == progress_data.material_id,
        Material.is_deleted == 0,
    ).first()

    if not material:
        return {
            "code": 30001,
            "message": "材料不存在",
        }

    # Get existing progress
    progress = db.query(WatchProgress).filter(
        WatchProgress.user_id == current_user.user_id,
        WatchProgress.material_id == progress_data.material_id,
    ).first()

    current_time = datetime.now()
    max_position = progress_data.max_position
    play_position = progress_data.play_position

    if progress:
        # Anti-cheating: ignore if trying to skip ahead more than 30 seconds
        if max_position > progress.max_position + 30:
            # Detected cheating, only update time, not position
            progress.last_watch_time = current_time
            db.commit()
            return {
                "code": 0,
                "data": {
                    "is_completed": bool(progress.is_completed),
                    "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
                },
            }

        # Update normal progress
        if max_position > progress.max_position:
            progress.max_position = max_position

        progress.watched_seconds = play_position
        progress.last_watch_time = current_time

        # Check completion (95% rule)
        if material.duration:
            completion_threshold = material.duration * 0.95
            if progress.max_position >= completion_threshold and not progress.is_completed:
                progress.is_completed = 1
                progress.completed_at = current_time
        elif progress.max_position >= 570:  # Fallback: 9.5 minutes
            if not progress.is_completed:
                progress.is_completed = 1
                progress.completed_at = current_time

    else:
        # Create new progress record
        record_id = f"R{uuid.uuid4().hex[:8].upper()}"
        progress = WatchProgress(
            record_id=record_id,
            user_id=current_user.user_id,
            material_id=progress_data.material_id,
            watched_seconds=play_position,
            max_position=max_position,
            total_duration=material.duration or 0,
            last_watch_time=current_time,
        )
        db.add(progress)

        # Check completion
        if material.duration:
            if max_position >= material.duration * 0.95:
                progress.is_completed = 1
                progress.completed_at = current_time
        elif max_position >= 570:
            progress.is_completed = 1
            progress.completed_at = current_time

    db.commit()

    return {
        "code": 0,
        "data": {
            "is_completed": bool(progress.is_completed),
            "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
        },
    }


@router.get("/hr/{project_id}/export")
async def export_progress(
    project_id: str,
    dept_id: Optional[str] = None,
    status: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Export learning progress for HR.
    """
    # Get project
    project = db.query(Project).filter(
        Project.project_id == project_id,
        Project.is_deleted == 0,
    ).first()

    if not project:
        return {
            "code": 20001,
            "message": "项目不存在",
        }

    # TODO: Implement full export with user filtering
    return {
        "code": 0,
        "data": {
            "project_id": project_id,
            "project_title": project.title,
            "export_time": datetime.now().isoformat(),
            "total_employees": 0,
            "list": [],
        },
    }