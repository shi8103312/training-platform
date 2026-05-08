"""
User API Routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.user import User
from ...models.department import Department
from ...api.deps import get_current_user
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