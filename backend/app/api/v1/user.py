"""
User API Routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...database import get_db
from ...models.user import User
from ...models.department import Department
from ...models.training import Project, Progress
from ...api.deps import get_current_user, require_hr_admin
from ...core.permissions import Role
from ...schemas.auth import UserInfo

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