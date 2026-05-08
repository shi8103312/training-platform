"""
Training Project API Routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from datetime import datetime
import uuid
import json

from ...database import get_db
from ...models.user import User
from ...models.training import Project, Material
from ...models.department import Department
from ...api.deps import get_current_user, require_hr_admin
from ...core.permissions import Role, check_user_access_to_project
from ...schemas.training import (
    CreateProjectRequest,
    UpdateProjectRequest,
    ProjectResponse,
    ProjectDetailResponse,
    MaterialResponse,
    ExamBasicResponse,
)

router = APIRouter(prefix="/training/project", tags=["培训管理"])


@router.get("/list")
async def get_project_list(
    status: Optional[int] = Query(None, ge=0, le=3),
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get training project list.

    - HR admin can see all projects
    - Employees can only see published projects
    """
    query = db.query(Project).filter(Project.is_deleted == 0)

    # Filter by status based on role
    if current_user.role != Role.HR_ADMIN:
        query = query.filter(Project.status == 1)  # Only published
    elif status is not None:
        query = query.filter(Project.status == status)

    # Search by keyword
    if keyword:
        query = query.filter(Project.title.like(f"%{keyword}%"))

    # Get total count
    total = query.count()

    # Pagination
    offset = (page - 1) * page_size
    projects = query.order_by(Project.create_time.desc()).offset(offset).limit(page_size).all()

    return {
        "code": 0,
        "data": {
            "list": [
                {
                    "project_id": p.project_id,
                    "title": p.title,
                    "description": p.description,
                    "cover_image": p.cover_image,
                    "status": p.status,
                    "status_text": p.status_text,
                    "is_required": bool(p.is_required),
                    "deadline": p.deadline.isoformat() if p.deadline else None,
                    "created_by": p.created_by,
                    "creator_name": p.creator.real_name if p.creator else None,
                    "published_at": p.published_at.isoformat() if p.published_at else None,
                    "create_time": p.create_time.isoformat() if p.create_time else None,
                }
                for p in projects
            ],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        },
    }


@router.get("/{project_id}")
async def get_project_detail(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get training project detail with materials and exam info.
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

    # Check access permission
    if current_user.role != Role.HR_ADMIN:
        if not check_user_access_to_project(current_user, project, db):
            return {
                "code": 10005,
                "message": "您没有权限访问此项目",
            }

        # Employees can only see published projects
        if project.status != 1:
            return {
                "code": 20001,
                "message": "项目不存在",
            }

    # Get materials
    materials = db.query(Material).filter(
        Material.project_id == project_id,
        Material.is_deleted == 0,
    ).order_by(Material.sort_order).all()

    # Get exam info
    exam_info = None
    if project.exams:
        exam = project.exams[0]  # Assume one exam per project
        exam_info = {
            "exam_id": exam.exam_id,
            "title": exam.title,
        }

    return {
        "code": 0,
        "data": {
            "project_id": project.project_id,
            "title": project.title,
            "description": project.description,
            "cover_image": project.cover_image,
            "status": project.status,
            "status_text": project.status_text,
            "is_required": bool(project.is_required),
            "push_scope": project.push_scope,
            "deadline": project.deadline.isoformat() if project.deadline else None,
            "created_by": project.created_by,
            "creator_name": project.creator.real_name if project.creator else None,
            "published_at": project.published_at.isoformat() if project.published_at else None,
            "create_time": project.create_time.isoformat() if project.create_time else None,
            "materials": [
                {
                    "material_id": m.material_id,
                    "title": m.title,
                    "material_type": m.material_type,
                    "material_type_text": "视频" if m.is_video else "文档",
                    "duration": m.duration,
                    "thumbnail": m.thumbnail_path,
                    "sort_order": m.sort_order,
                }
                for m in materials
            ],
            "exam": exam_info,
        },
    }


@router.post("")
async def create_project(
    project_data: CreateProjectRequest,
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Create a new training project (HR admin only).
    """
    # Check title uniqueness under same status
    existing = db.query(Project).filter(
        Project.title == project_data.title,
        Project.status == 0,  # Draft status
        Project.is_deleted == 0,
    ).first()

    if existing:
        return {
            "code": 20002,
            "message": "该项目名称已存在",
        }

    # Generate project ID
    project_id = f"P{uuid.uuid4().hex[:8].upper()}"

    # Create project
    project = Project(
        project_id=project_id,
        title=project_data.title,
        description=project_data.description,
        cover_image=project_data.cover_image,
        deadline=project_data.deadline,
        is_required=1 if project_data.is_required else 0,
        push_scope=json.dumps(project_data.push_scope.model_dump()),
        created_by=current_user.user_id,
        status=0,  # Draft
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return {
        "code": 0,
        "data": {
            "project_id": project.project_id,
            "status": project.status,
        },
    }


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    project_data: UpdateProjectRequest,
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Update a training project (HR admin only).
    Cannot edit published projects.
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

    # Cannot edit published projects
    if project.status == 1:
        return {
            "code": 20003,
            "message": "已发布项目需先下架才能编辑",
        }

    # Update fields
    if project_data.title is not None:
        # Check title uniqueness
        existing = db.query(Project).filter(
            Project.title == project_data.title,
            Project.project_id != project_id,
            Project.status == project.status,
            Project.is_deleted == 0,
        ).first()
        if existing:
            return {
                "code": 20002,
                "message": "该项目名称已存在",
            }
        project.title = project_data.title

    if project_data.description is not None:
        project.description = project_data.description

    if project_data.cover_image is not None:
        project.cover_image = project_data.cover_image

    if project_data.deadline is not None:
        project.deadline = project_data.deadline

    if project_data.is_required is not None:
        project.is_required = 1 if project_data.is_required else 0

    if project_data.push_scope is not None:
        project.push_scope = json.dumps(project_data.push_scope.model_dump())

    db.commit()

    return {
        "code": 0,
        "message": "更新成功",
    }


@router.post("/{project_id}/publish")
async def publish_project(
    project_id: str,
    send_notification: bool = False,
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Publish a training project (HR admin only).

    Prerequisites:
    - Project must be in draft status
    - Project must have at least one material
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

    if project.status != 0:
        return {
            "code": 20005,
            "message": "只能发布草稿状态的项目",
        }

    # Check materials
    materials = db.query(Material).filter(
        Material.project_id == project_id,
        Material.is_deleted == 0,
    ).all()

    if len(materials) == 0:
        return {
            "code": 20006,
            "message": "项目至少包含一个材料",
        }

    # Publish
    project.status = 1
    project.published_at = datetime.now()
    db.commit()

    # TODO: Send notification if requested
    if send_notification:
        pass  # Implement notification sending

    return {
        "code": 0,
        "message": "发布成功",
    }


@router.post("/{project_id}/unpublish")
async def unpublish_project(
    project_id: str,
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Unpublish a training project (HR admin only).
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

    if project.status != 1:
        return {
            "code": 20005,
            "message": "只能下架已发布的项目",
        }

    # Unpublish
    project.status = 2
    db.commit()

    return {
        "code": 0,
        "message": "下架成功",
    }


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Delete a training project (HR admin only).
    Only draft projects can be deleted. Published projects must be unpublished first.
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

    # Can only delete draft projects
    if project.status != 0:
        return {
            "code": 20004,
            "message": "已发布项目需先下架才能删除",
        }

    # Soft delete
    project.is_deleted = 1
    db.commit()

    return {
        "code": 0,
        "message": "删除成功",
    }