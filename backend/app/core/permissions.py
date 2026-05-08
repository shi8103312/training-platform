"""
Permission Decorators and Utilities
"""
from functools import wraps
from typing import List, Callable

from fastapi import Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..core.exceptions import raise_permission_denied_error


class Role:
    """
    Role constants.
    """
    HR_ADMIN = 1
    EMPLOYEE = 2


def require_role(*roles: int):
    """
    Decorator to require specific roles.
    Usage: @require_role(Role.HR_ADMIN)
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find current_user in kwargs or args
            current_user = kwargs.get("current_user")
            if current_user is None:
                for arg in args:
                    if hasattr(arg, "role"):
                        current_user = arg
                        break

            if current_user is None:
                raise_permission_denied_error()

            if current_user.role not in roles:
                raise_permission_denied_error()

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_hr_admin():
    """
    Decorator to require HR_ADMIN role.
    """
    return require_role(Role.HR_ADMIN)


def check_user_access_to_project(user, project, db: Session) -> bool:
    """
    Check if user has access to a specific project.

    Args:
        user: Current user object
        project: Project object
        db: Database session

    Returns:
        bool: True if user has access
    """
    # HR_ADMIN has access to all projects
    if user.role == Role.HR_ADMIN:
        return True

    # Check push scope
    import json

    push_scope = project.push_scope
    if isinstance(push_scope, str):
        push_scope = json.loads(push_scope)

    scope_type = push_scope.get("type")

    if scope_type == "all":
        return True

    if scope_type == "departments":
        # Check if user's department is in the scope
        user_dept_id = user.dept_id
        target_depts = push_scope.get("departments", [])

        # Check direct department
        if user_dept_id in target_depts:
            return True

        # Check if user's department is a child of any target department
        from ..models.department import Department

        for target_dept_id in target_depts:
            if _is_descendant_department(db, user_dept_id, target_dept_id):
                return True

    elif scope_type == "users":
        target_users = push_scope.get("users", [])
        if user.user_id in target_users:
            return True

    return False


def _is_descendant_department(
    db: Session, dept_id: str, ancestor_id: str
) -> bool:
    """
    Check if dept_id is a descendant of ancestor_id.
    """
    from ..models.department import Department

    current = db.query(Department).filter(Department.dept_id == dept_id).first()

    while current and current.parent_id:
        if current.parent_id == ancestor_id:
            return True
        current = db.query(Department).filter(
            Department.dept_id == current.parent_id
        ).first()

    return False