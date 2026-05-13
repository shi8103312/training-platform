"""
Department API Routes
"""
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from ...database import get_db
from ...models.department import Department
from ...models.user import User
from ...api.deps import get_current_user, require_hr_admin
from ...schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentTreeResponse,
    ImportResultResponse,
    ImportError,
)

router = APIRouter(prefix="/department", tags=["部门"])


def _build_department_tree(
    departments: List[Department],
    parent_id: Optional[str] = None,
) -> List[DepartmentTreeResponse]:
    """
    Build department tree recursively.
    """
    tree = []
    for dept in departments:
        if dept.parent_id == parent_id:
            children = _build_department_tree(departments, dept.dept_id)
            tree.append(
                DepartmentTreeResponse(
                    dept_id=dept.dept_id,
                    dept_code=dept.dept_code,
                    dept_name=dept.dept_name,
                    parent_id=dept.parent_id,
                    sort_order=dept.sort_order,
                    status=dept.status,
                    dept_level=dept.dept_level,
                    children=children,
                )
            )
    return tree


@router.get("/tree")
async def get_department_tree(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get department tree structure.
    """
    departments = db.query(Department).filter(Department.status == 1).all()
    tree = _build_department_tree(departments, None)

    return {
        "code": 0,
        "data": tree,
    }


@router.get("/list")
async def get_department_list(
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Get flat department list (HR admin only).
    """
    departments = db.query(Department).all()

    return {
        "code": 0,
        "data": [
            {
                "dept_id": dept.dept_id,
                "dept_code": dept.dept_code,
                "dept_name": dept.dept_name,
                "parent_id": dept.parent_id,
                "dept_level": dept.dept_level,
                "sort_order": dept.sort_order,
                "status": dept.status,
            }
            for dept in departments
        ],
    }


@router.post("")
async def create_department(
    dept_data: DepartmentCreate,
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Create a new department (HR admin only).
    """
    # Check if code already exists
    existing = db.query(Department).filter(
        Department.dept_code == dept_data.dept_code
    ).first()
    if existing:
        return {
            "code": 12002,
            "message": "部门编码已存在",
        }

    # Validate parent exists
    # Handle empty string parent_id
    parent_id = dept_data.parent_id if dept_data.parent_id else None

    if parent_id:
        parent = db.query(Department).filter(
            Department.dept_id == parent_id
        ).first()
        if not parent:
            return {
                "code": 12001,
                "message": "上级部门不存在",
            }
        level = parent.dept_level + 1
    else:
        level = 1

    # Calculate dept_id
    import uuid
    dept_id = f"D{uuid.uuid4().hex[:8].upper()}"

    # Create department
    dept = Department(
        dept_id=dept_id,
        dept_code=dept_data.dept_code,
        dept_name=dept_data.dept_name,
        parent_id=parent_id,
        dept_level=level,
        sort_order=dept_data.sort_order,
        status=dept_data.status,
    )

    db.add(dept)
    db.commit()
    db.refresh(dept)

    return {
        "code": 0,
        "data": {
            "dept_id": dept.dept_id,
        },
    }


@router.put("/{dept_id}")
async def update_department(
    dept_id: str,
    dept_data: DepartmentUpdate,
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Update a department (HR admin only).
    """
    dept = db.query(Department).filter(Department.dept_id == dept_id).first()
    if not dept:
        return {
            "code": 12001,
            "message": "部门不存在",
        }

    # Update fields
    if dept_data.dept_name is not None:
        dept.dept_name = dept_data.dept_name
    if dept_data.sort_order is not None:
        dept.sort_order = dept_data.sort_order
    if dept_data.status is not None:
        dept.status = dept_data.status

    # Handle parent change
    if dept_data.parent_id is not None and dept_data.parent_id != dept.parent_id:
        # Check for circular reference
        if _would_create_cycle(db, dept_id, dept_data.parent_id):
            return {
                "code": 12004,
                "message": "不能将部门设置为自己的下级部门",
            }

        # Update level
        if dept_data.parent_id:
            parent = db.query(Department).filter(
                Department.dept_id == dept_data.parent_id
            ).first()
            if not parent:
                return {
                    "code": 12001,
                    "message": "上级部门不存在",
                }
            new_level = parent.dept_level + 1
        else:
            new_level = 1

        dept.parent_id = dept_data.parent_id
        dept.dept_level = new_level

        # Update descendants' levels
        _update_descendant_levels(db, dept_id, dept.dept_level - new_level)

    db.commit()

    return {
        "code": 0,
        "message": "更新成功",
    }


def _would_create_cycle(db: Session, dept_id: str, new_parent_id: str) -> bool:
    """
    Check if setting new_parent_id as parent of dept_id would create a cycle.
    """
    if dept_id == new_parent_id:
        return True

    current_id = new_parent_id
    visited = {dept_id}

    while current_id:
        if current_id in visited:
            return True
        visited.add(current_id)

        dept = db.query(Department).filter(
            Department.dept_id == current_id
        ).first()
        if not dept:
            return False
        current_id = dept.parent_id

    return False


def _update_descendant_levels(db: Session, parent_id: str, level_delta: int):
    """
    Update levels of all descendants.
    """
    children = db.query(Department).filter(
        Department.parent_id == parent_id
    ).all()

    for child in children:
        child.dept_level += level_delta
        _update_descendant_levels(db, child.dept_id, level_delta)


@router.delete("/{dept_id}")
async def delete_department(
    dept_id: str,
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Delete a department (HR admin only).
    Cannot delete if department has children or users.
    """
    dept = db.query(Department).filter(Department.dept_id == dept_id).first()
    if not dept:
        return {
            "code": 12001,
            "message": "部门不存在",
        }

    # Check for children
    has_children = db.query(Department).filter(
        Department.parent_id == dept_id
    ).first() is not None
    if has_children:
        return {
            "code": 12003,
            "message": "该部门存在下级部门，无法删除",
        }

    # Check for users
    has_users = db.query(User).filter(User.dept_id == dept_id).first() is not None
    if has_users:
        return {
            "code": 12003,
            "message": "该部门存在员工，无法删除",
        }

    db.delete(dept)
    db.commit()

    return {
        "code": 0,
        "message": "删除成功",
    }


@router.post("/import")
async def import_departments(
    file: UploadFile = File(...),
    mode: str = "simulate",
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Import departments from Excel file (HR admin only).

    Format: dept_code|dept_name|parent_code|sort_order|status
    """
    import io
    import openpyxl

    if not file.filename.endswith((".xlsx", ".xls")):
        return {
            "code": 12004,
            "message": "请上传Excel文件",
        }

    # Read file content
    content = await file.read()
    wb = openpyxl.load_workbook(io.BytesIO(content))
    ws = wb.active

    errors = []
    success_count = 0
    total_count = 0

    # Parse rows (skip header)
    for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        total_count += 1

        if not row[0]:
            continue

        dept_code = str(row[0]).strip()
        dept_name = str(row[1]).strip() if row[1] else ""
        parent_code = str(row[2]).strip() if row[2] else None
        sort_order = int(row[3]) if row[3] else 0
        status = int(row[4]) if row[4] and row[4] in [0, 1] else 1

        # Validate
        if not dept_name:
            errors.append(ImportError(row=row_num, dept_code=dept_code, error="部门名称不能为空"))
            continue

        # Check if exists
        existing = db.query(Department).filter(
            Department.dept_code == dept_code
        ).first()

        if existing:
            if mode in ["update", "simulate"]:
                if mode == "update":
                    existing.dept_name = dept_name
                    existing.sort_order = sort_order
                    existing.status = status
                    success_count += 1
                else:
                    errors.append(ImportError(row=row_num, dept_code=dept_code, error="部门已存在，将更新"))
            else:
                errors.append(ImportError(row=row_num, dept_code=dept_code, error="部门已存在"))
            continue

        # Validate parent
        parent_id = None
        level = 1
        if parent_code:
            parent = db.query(Department).filter(
                Department.dept_code == parent_code
            ).first()
            if parent:
                parent_id = parent.dept_id
                level = parent.dept_level + 1
            else:
                if mode != "simulate":
                    errors.append(ImportError(row=row_num, dept_code=dept_code, error=f"上级部门编码不存在"))
                    continue

        # Create department
        import uuid
        dept_id = f"D{uuid.uuid4().hex[:8].upper()}"

        if mode != "simulate":
            dept = Department(
                dept_id=dept_id,
                dept_code=dept_code,
                dept_name=dept_name,
                parent_id=parent_id,
                dept_level=level,
                sort_order=sort_order,
                status=status,
            )
            db.add(dept)

        success_count += 1

    if mode != "simulate":
        db.commit()

    return ImportResultResponse(
        code=0,
        data={
            "mode": mode,
            "total": total_count,
            "success": success_count,
            "failed": len(errors),
            "errors": errors,
        },
    )