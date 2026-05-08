"""
Learning Progress API Routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import json

from ...database import get_db
from ...models.user import User
from ...models.department import Department
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
    Export learning progress for HR report.
    Returns progress list with filtering by department and status.
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

    # Get project materials
    materials = db.query(Material).filter(
        Material.project_id == project_id,
        Material.is_deleted == 0,
    ).all()
    material_ids = [m.material_id for m in materials]
    total_materials = len(materials)

    # Build query for users who should see this project
    # Based on push_scope: {"type": "all"} or {"type": "departments", "dept_ids": [...]} or {"type": "users", "user_ids": [...]}
    push_scope = json.loads(project.push_scope) if isinstance(project.push_scope, str) else project.push_scope

    user_query = db.query(User).filter(User.status == 1)  # Only active users

    if push_scope.get("type") == "departments":
        dept_ids = push_scope.get("dept_ids", [])
        if dept_ids:
            user_query = user_query.filter(User.dept_id.in_(dept_ids))
    elif push_scope.get("type") == "users":
        user_ids = push_scope.get("user_ids", [])
        if user_ids:
            user_query = user_query.filter(User.user_id.in_(user_ids))
    # For "all" type, we don't filter by department

    # Apply department filter
    if dept_id:
        user_query = user_query.filter(User.dept_id == dept_id)

    # Get total count before pagination
    total_employees = user_query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    users = user_query.offset(offset).limit(page_size).all()

    # Get all user IDs
    user_ids = [u.user_id for u in users]

    # Get watch progress for all materials
    watch_progress_map = {}
    if material_ids and user_ids:
        watch_records = db.query(WatchProgress).filter(
            WatchProgress.material_id.in_(material_ids),
            WatchProgress.user_id.in_(user_ids),
        ).all()
        for wp in watch_records:
            if wp.user_id not in watch_progress_map:
                watch_progress_map[wp.user_id] = {}
            watch_progress_map[wp.user_id][wp.material_id] = wp

    # Get exam attempts
    exam = db.query(Exam).filter(Exam.project_id == project_id, Exam.is_deleted == 0).first()
    exam_attempts_map = {}
    if exam and user_ids:
        attempts = db.query(ExamAttempt).filter(
            ExamAttempt.exam_id == exam.exam_id,
            ExamAttempt.user_id.in_(user_ids),
        ).all()
        # Get best score for each user
        for a in attempts:
            if a.user_id not in exam_attempts_map or (a.score and a.score > exam_attempts_map[a.user_id].score):
                exam_attempts_map[a.user_id] = a

    # Build result list
    result_list = []
    stats = {"total": 0, "completed": 0, "in_progress": 0, "not_started": 0}

    for user in users:
        user_wp = watch_progress_map.get(user.user_id, {})
        completed_count = 0
        total_progress = 0
        total_time = 0

        for m in materials:
            wp = user_wp.get(m.material_id)
            if wp:
                if wp.is_completed:
                    completed_count += 1
                total_progress += wp.progress_percentage
                total_time += wp.watched_seconds

        # Calculate overall progress percentage
        progress_pct = int(total_progress / total_materials) if total_materials > 0 else 0

        # Determine status
        if progress_pct == 0:
            overall_status = 0  # Not started
        elif progress_pct >= 100:
            overall_status = 2  # Completed
        else:
            overall_status = 1  # In progress

        # Apply status filter
        if status is not None and overall_status != status:
            continue

        stats["total"] += 1
        if overall_status == 2:
            stats["completed"] += 1
        elif overall_status == 1:
            stats["in_progress"] += 1
        else:
            stats["not_started"] += 1

        # Get exam score
        exam_score = None
        attempt = exam_attempts_map.get(user.user_id)
        if attempt and attempt.score is not None:
            exam_score = attempt.score

        # Get department name
        dept = db.query(Department).filter(Department.dept_id == user.dept_id).first()
        dept_name = dept.dept_name if dept else ""

        # Format learning time
        if total_time > 0:
            hours = total_time // 3600
            minutes = (total_time % 3600) // 60
            learning_time = f"{hours}小时{minutes}分" if hours > 0 else f"{minutes}分钟"
        else:
            learning_time = "0"

        result_list.append({
            "user_id": user.user_id,
            "user_name": user.real_name,
            "dept_id": user.dept_id,
            "dept_name": dept_name,
            "project_title": project.title,
            "progress": progress_pct,
            "learning_time": learning_time,
            "exam_score": exam_score,
            "status": overall_status,
            "status_text": ["未开始", "进行中", "已完成"][overall_status],
        })

    # Get department list for filter
    departments = db.query(Department).filter(Department.status == 1).all()

    return {
        "code": 0,
        "data": {
            "project_id": project_id,
            "project_title": project.title,
            "export_time": datetime.now().isoformat(),
            "stats": stats,
            "total_employees": total_employees,
            "list": result_list,
            "departments": [
                {"dept_id": d.dept_id, "dept_name": d.dept_name}
                for d in departments
            ],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_employees,
                "total_pages": (total_employees + page_size - 1) // page_size,
            },
        },
    }


@router.get("/hr/stats/{project_id}")
async def get_progress_stats(
    project_id: str,
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Get progress statistics for a project (for charts).
    """
    project = db.query(Project).filter(
        Project.project_id == project_id,
        Project.is_deleted == 0,
    ).first()

    if not project:
        return {
            "code": 20001,
            "message": "项目不存在",
        }

    # Get project materials
    materials = db.query(Material).filter(
        Material.project_id == project_id,
        Material.is_deleted == 0,
    ).all()
    material_ids = [m.material_id for m in materials]
    total_materials = len(materials)

    # Get push scope
    push_scope = json.loads(project.push_scope) if isinstance(project.push_scope, str) else project.push_scope

    user_query = db.query(User).filter(User.status == 1)

    if push_scope.get("type") == "departments":
        dept_ids = push_scope.get("dept_ids", [])
        if dept_ids:
            user_query = user_query.filter(User.dept_id.in_(dept_ids))
    elif push_scope.get("type") == "users":
        user_ids = push_scope.get("user_ids", [])
        if user_ids:
            user_query = user_query.filter(User.user_id.in_(user_ids))

    users = user_query.all()
    user_ids = [u.user_id for u in users]

    # Get watch progress
    watch_progress_map = {}
    if material_ids and user_ids:
        watch_records = db.query(WatchProgress).filter(
            WatchProgress.material_id.in_(material_ids),
            WatchProgress.user_id.in_(user_ids),
        ).all()
        for wp in watch_records:
            if wp.user_id not in watch_progress_map:
                watch_progress_map[wp.user_id] = {}
            watch_progress_map[wp.user_id][wp.material_id] = wp

    # Calculate stats
    stats = {"total": len(users), "completed": 0, "in_progress": 0, "not_started": 0}
    for user in users:
        user_wp = watch_progress_map.get(user.user_id, {})
        completed_count = 0
        total_progress = 0

        for m in materials:
            wp = user_wp.get(m.material_id)
            if wp:
                if wp.is_completed:
                    completed_count += 1
                total_progress += wp.progress_percentage

        progress_pct = int(total_progress / total_materials) if total_materials > 0 else 0

        if progress_pct == 0:
            stats["not_started"] += 1
        elif progress_pct >= 100:
            stats["completed"] += 1
        else:
            stats["in_progress"] += 1

    # Calculate completion rate
    completion_rate = int((stats["completed"] / stats["total"] * 100)) if stats["total"] > 0 else 0

    # Get last 7 days trend
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_completions = db.query(WatchProgress).filter(
        WatchProgress.material_id.in_(material_ids),
        WatchProgress.is_completed == 1,
        WatchProgress.completed_at >= seven_days_ago,
    ).all()

    # Group by date
    trend = {i: 0 for i in range(7)}
    for wc in recent_completions:
        if wc.completed_at:
            day_idx = (datetime.now() - wc.completed_at).days
            if 0 <= day_idx < 7:
                trend[6 - day_idx] += 1

    return {
        "code": 0,
        "data": {
            "stats": stats,
            "completion_rate": completion_rate,
            "trend": list(trend.values()),
        },
    }