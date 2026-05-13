"""
User API Routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
from datetime import datetime, timedelta

from ...database import get_db
from ...models.user import User
from ...models.department import Department
from ...models.training import Project, Progress
from ...api.deps import get_current_user, require_hr_admin
from ...core.permissions import Role
from ...core.security import hash_password
from ...schemas.auth import UserInfo, UserCreate, UserUpdate

router = APIRouter(prefix="/user", tags=["用户"])


@router.get("/info")
async def get_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get current user information with department details.
    """
    # Get department info
    dept = db.query(Department).filter(Department.dept_id == current_user.dept_id).first()

    dept_name = None
    dept_path = None
    if dept:
        dept_name = dept.dept_name
        dept_path = dept.get_dept_path()

    return {
        "code": 0,
        "data": {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "real_name": current_user.real_name,
            "email": current_user.email,
            "phone": current_user.phone,
            "role": current_user.role,
            "role_text": "HR管理员" if current_user.role == Role.HR_ADMIN else "员工",
            "dept_id": current_user.dept_id,
            "dept_name": dept_name,
            "dept_path": dept_path,
            "avatar": current_user.avatar,
        },
    }


@router.get("/stats/dashboard")
async def get_dashboard_stats(
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Get dashboard statistics for HR admin.
    Returns counts for projects, employees, pending, and completion rate.
    """
    # Count published projects
    project_count = db.query(Project).filter(
        Project.status == 1,
        Project.is_deleted == 0,
    ).count()

    # Count active employees
    employee_count = db.query(User).filter(
        User.status == 1,
        User.role == 2,  # Only employees
    ).count()

    # Count completed progress
    completed_count = db.query(Progress).filter(
        Progress.overall_status == 2,
    ).count()

    # Count in-progress
    in_progress_count = db.query(Progress).filter(
        Progress.overall_status == 1,
    ).count()

    # Total progress records
    total_progress = db.query(Progress).count()

    # Calculate completion rate
    completion_rate = int((completed_count / total_progress * 100)) if total_progress > 0 else 0

    return {
        "code": 0,
        "data": {
            "project_count": project_count,
            "employee_count": employee_count,
            "pending_count": in_progress_count,
            "completion_rate": completion_rate,
        },
    }


@router.get("/stats/projects")
async def get_project_stats(
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Get statistics for all published projects.
    Returns enrollment count, completion count, and completion rate per project.
    """
    from ...models.training import Project, Material, WatchProgress

    # Get all published projects
    projects = db.query(Project).filter(
        Project.status == 1,
        Project.is_deleted == 0,
    ).all()

    project_stats = []
    for project in projects:
        # Get project materials
        materials = db.query(Material).filter(
            Material.project_id == project.project_id,
            Material.is_deleted == 0,
        ).all()
        material_ids = [m.material_id for m in materials]
        total_materials = len(materials)

        # Get push scope to determine target users
        try:
            push_scope = json.loads(project.push_scope) if isinstance(project.push_scope, str) else project.push_scope
        except (json.JSONDecodeError, TypeError):
            push_scope = {}

        push_scope_type = push_scope.get("type") if push_scope else None

        # Build user query based on push_scope
        user_query = db.query(User).filter(User.status == 1, User.role == 2)

        if push_scope_type == "departments":
            dept_ids = push_scope.get("dept_ids", [])
            if dept_ids:
                user_query = user_query.filter(User.dept_id.in_(dept_ids))
        elif push_scope_type == "users":
            user_ids = push_scope.get("user_ids", [])
            if user_ids:
                user_query = user_query.filter(User.user_id.in_(user_ids))
        # For "all" type or no type, no additional filter

        target_users = user_query.all()
        total_enrolled = len(target_users)
        user_ids = [u.user_id for u in target_users]

        # Count completions
        completed_count = 0
        in_progress_count = 0

        if material_ids and user_ids:
            # Get all watch progress for this project's materials and users
            watch_records = db.query(WatchProgress).filter(
                WatchProgress.material_id.in_(material_ids),
                WatchProgress.user_id.in_(user_ids),
            ).all()

            # Build progress map per user
            user_progress = {}
            for wp in watch_records:
                if wp.user_id not in user_progress:
                    user_progress[wp.user_id] = {}
                user_progress[wp.user_id][wp.material_id] = wp

            # Calculate completion status per user
            for user_id in user_ids:
                user_wp = user_progress.get(user_id, {})
                user_completed = 0
                for m in materials:
                    wp = user_wp.get(m.material_id)
                    if wp and wp.is_completed:
                        user_completed += 1

                if user_completed == total_materials and total_materials > 0:
                    completed_count += 1
                elif user_completed > 0:
                    in_progress_count += 1

        completion_rate = int((completed_count / total_enrolled * 100)) if total_enrolled > 0 else 0

        project_stats.append({
            "project_id": project.project_id,
            "title": project.title,
            "is_required": project.is_required,
            "status": project.status,
            "status_text": project.status_text,
            "deadline": project.deadline.isoformat() if project.deadline else None,
            "enrolled_count": total_enrolled,
            "completed_count": completed_count,
            "in_progress_count": in_progress_count,
            "completion_rate": completion_rate,
        })

    return {
        "code": 0,
        "data": project_stats,
    }


@router.get("/stats/trend")
async def get_learning_trend(
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Get learning trend for the last 7 days.
    Returns the number of users who completed at least one material each day.
    """
    from ...models.training import WatchProgress

    # Get last 7 days trend
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_records = db.query(WatchProgress).filter(
        WatchProgress.is_completed == 1,
        WatchProgress.completed_at >= seven_days_ago,
    ).all()

    # Group by date
    trend = {i: 0 for i in range(7)}
    for record in recent_records:
        if record.completed_at:
            day_idx = (datetime.now() - record.completed_at).days
            if 0 <= day_idx < 7:
                trend[6 - day_idx] += 1

    return {
        "code": 0,
        "data": {
            "trend": list(trend.values()),
        },
    }


@router.get("/list")
async def get_user_list(
    dept_id: str = Query(None),
    role: int = Query(None),
    status: int = Query(1),
    keyword: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Get user list for HR admin.
    """
    query = db.query(User)

    if dept_id:
        query = query.filter(User.dept_id == dept_id)
    if role is not None:
        query = query.filter(User.role == role)
    if status is not None:
        query = query.filter(User.status == status)
    if keyword:
        query = query.filter(User.real_name.like(f"%{keyword}%"))

    total = query.count()
    offset = (page - 1) * page_size
    users = query.offset(offset).limit(page_size).all()

    return {
        "code": 0,
        "data": [
            {
                "user_id": u.user_id,
                "username": u.username,
                "real_name": u.real_name,
                "email": u.email,
                "phone": u.phone,
                "role": u.role,
                "dept_id": u.dept_id,
                "dept_name": u.department.dept_name if u.department else None,
                "status": u.status,
            }
            for u in users
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }


@router.post("")
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Create a new user (HR admin only).
    """
    # Check if username already exists
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        return {"code": 13001, "message": "用户名已存在"}

    # Validate department exists
    if user_data.dept_id:
        dept = db.query(Department).filter(Department.dept_id == user_data.dept_id).first()
        if not dept:
            return {"code": 13002, "message": "部门不存在"}

    # Generate user_id
    import uuid
    user_id = f"U{uuid.uuid4().hex[:8].upper()}"

    # Hash password
    password_hash = hash_password(user_data.password)

    # Create user
    user = User(
        user_id=user_id,
        username=user_data.username,
        password_hash=password_hash,
        real_name=user_data.real_name,
        email=user_data.email or f"{user_data.username}@example.com",
        phone=user_data.phone,
        dept_id=user_data.dept_id,
        role=user_data.role,
        status=user_data.status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"code": 0, "data": {"user_id": user.user_id}}


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Update a user (HR admin only).
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return {"code": 13003, "message": "用户不存在"}

    # Update fields
    if user_data.real_name is not None:
        user.real_name = user_data.real_name
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.phone is not None:
        user.phone = user_data.phone
    if user_data.dept_id is not None:
        if user_data.dept_id:
            dept = db.query(Department).filter(Department.dept_id == user_data.dept_id).first()
            if not dept:
                return {"code": 13002, "message": "部门不存在"}
        user.dept_id = user_data.dept_id
    if user_data.role is not None:
        user.role = user_data.role
    if user_data.status is not None:
        user.status = user_data.status
    if user_data.password is not None:
        from passlib.context import CryptContext
        user.password_hash = hash_password(user_data.password)

    db.commit()
    return {"code": 0, "message": "更新成功"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Delete a user (HR admin only).
    """
    if user_id == current_user.user_id:
        return {"code": 13004, "message": "不能删除自己"}

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return {"code": 13003, "message": "用户不存在"}

    # Soft delete - set status to 0
    user.status = 0
    db.commit()
    return {"code": 0, "message": "删除成功"}