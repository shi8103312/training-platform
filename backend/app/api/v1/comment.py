"""
Comment API Routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import uuid

from ...database import get_db
from ...models.user import User
from ...models.training import Project, Comment
from ...api.deps import get_current_user
from ...core.permissions import Role
from ...schemas.training import CreateCommentRequest, CommentResponse

router = APIRouter(prefix="/comment", tags=["评论"])


@router.get("/{project_id}")
async def get_comments(
    project_id: str,
    material_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get comments for a project or material.

    Supports filtering by material_id.
    Returns comments with nested replies (max 2 levels).
    """
    query = db.query(Comment).filter(
        Comment.project_id == project_id,
        Comment.is_deleted == 0,
        Comment.status == 1,
    )

    if material_id:
        query = query.filter(Comment.material_id == material_id)
    else:
        query = query.filter(Comment.material_id == None)

    # Get top-level comments (no parent)
    query = query.filter(Comment.parent_id == None)

    total = query.count()
    comments = query.order_by(Comment.create_time.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # Build response with replies
    result = []
    for c in comments:
        # Get replies (one level)
        replies = db.query(Comment).filter(
            Comment.parent_id == c.comment_id,
            Comment.is_deleted == 0,
            Comment.status == 1,
        ).order_by(Comment.create_time.asc()).all()

        reply_list = []
        for r in replies:
            reply_list.append({
                "comment_id": r.comment_id,
                "project_id": r.project_id,
                "material_id": r.material_id,
                "user_id": r.user_id,
                "user_name": r.user.real_name if r.user else "未知",
                "content": r.content,
                "parent_id": r.parent_id,
                "like_count": r.like_count,
                "reply_count": 0,
                "create_time": r.create_time.isoformat() if r.create_time else None,
                "replies": [],
            })

        result.append({
            "comment_id": c.comment_id,
            "project_id": c.project_id,
            "material_id": c.material_id,
            "user_id": c.user_id,
            "user_name": c.user.real_name if c.user else "未知",
            "content": c.content,
            "parent_id": c.parent_id,
            "like_count": c.like_count,
            "reply_count": len(replies),
            "create_time": c.create_time.isoformat() if c.create_time else None,
            "replies": reply_list,
        })

    return {
        "code": 0,
        "data": {
            "list": result,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
            },
        },
    }


@router.post("")
async def create_comment(
    comment_data: CreateCommentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a comment or reply.

    - Content: max 500 characters
    - Replies: max 2 levels (parent_id)
    """
    # Validate content length
    if len(comment_data.content) > 500:
        return {
            "code": 90001,
            "message": "评论内容不能超过500字符",
        }

    # Validate project exists
    project = db.query(Project).filter(
        Project.project_id == comment_data.project_id,
        Project.is_deleted == 0,
    ).first()

    if not project:
        return {
            "code": 20001,
            "message": "项目不存在",
        }

    # Validate parent comment if replying
    if comment_data.parent_id:
        parent = db.query(Comment).filter(
            Comment.comment_id == comment_data.parent_id,
            Comment.is_deleted == 0,
        ).first()

        if not parent:
            return {
                "code": 60001,
                "message": "父评论不存在",
            }

        # Check nesting level (max 2)
        if parent.parent_id:
            # This is already a reply, cannot reply to a reply
            return {
                "code": 60001,
                "message": "回复不能超过2层",
            }

    # Generate comment ID
    comment_id = f"C{uuid.uuid4().hex[:8].upper()}"

    # Create comment
    comment = Comment(
        comment_id=comment_id,
        project_id=comment_data.project_id,
        material_id=comment_data.material_id,
        user_id=current_user.user_id,
        content=comment_data.content,
        parent_id=comment_data.parent_id,
    )

    db.add(comment)

    # Update parent reply count
    if comment_data.parent_id:
        parent = db.query(Comment).filter(
            Comment.comment_id == comment_data.parent_id
        ).first()
        if parent:
            parent.reply_count += 1

    db.commit()

    return {
        "code": 0,
        "data": {
            "comment_id": comment_id,
        },
    }


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a comment.

    - Employees can only delete their own comments
    - HR admins can delete any comment
    """
    comment = db.query(Comment).filter(
        Comment.comment_id == comment_id,
        Comment.is_deleted == 0,
    ).first()

    if not comment:
        return {
            "code": 60001,
            "message": "评论不存在",
        }

    # Check permission
    if current_user.role != Role.HR_ADMIN and comment.user_id != current_user.user_id:
        return {
            "code": 60002,
            "message": "您没有权限删除此评论",
        }

    # Soft delete
    comment.is_deleted = 1
    db.commit()

    return {
        "code": 0,
        "message": "删除成功",
    }