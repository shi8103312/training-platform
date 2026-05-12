"""
Comment API Routes
"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from slowapi import Limiter
from slowapi.util import get_remote_address
import uuid
import re

from ...database import get_db
from ...models.user import User
from ...models.training import Project, Comment
from ...api.deps import get_current_user
from ...core.permissions import Role
from ...schemas.training import CreateCommentRequest

router = APIRouter(prefix="/comment", tags=["评论"])

# Rate limiter for comment endpoints
comment_limiter = Limiter(key_func=get_remote_address)


def parse_mentions(content: str) -> List[str]:
    """
    Parse @mentions from content.
    Returns list of mentioned usernames.
    """
    pattern = r'@(\S+)'
    matches = re.findall(pattern, content)
    return matches


def get_mentioned_users(usernames: List[str], db: Session) -> List[dict]:
    """
    Get user info for mentioned usernames.
    Returns list of {user_id, real_name}.
    """
    if not usernames:
        return []

    users = db.query(User).filter(User.username.in_(usernames)).all()
    return [
        {"user_id": u.user_id, "real_name": u.real_name}
        for u in users
    ]


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
            # Parse mentions for reply
            mention_usernames = parse_mentions(r.content)
            mention_users = get_mentioned_users(mention_usernames, db)

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
                "mention_users": mention_users,
                "create_time": r.create_time.isoformat() if r.create_time else None,
                "replies": [],
            })

        # Parse mentions for comment
        mention_usernames = parse_mentions(c.content)
        mention_users = get_mentioned_users(mention_usernames, db)

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
            "mention_users": mention_users,
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
@comment_limiter.limit("10/minute")
async def create_comment(
    request: Request,
    comment_data: CreateCommentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a comment or reply.
    Rate limited to 10 comments per minute per IP.
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

    # Parse @mentions from content
    mentioned_usernames = parse_mentions(comment_data.content)
    mentioned_users = get_mentioned_users(mentioned_usernames, db)
    mention_user_ids = ",".join([u["user_id"] for u in mentioned_users]) if mentioned_users else None

    # Create comment
    comment = Comment(
        comment_id=comment_id,
        project_id=comment_data.project_id,
        material_id=comment_data.material_id,
        user_id=current_user.user_id,
        content=comment_data.content,
        parent_id=comment_data.parent_id,
        mention_user_ids=mention_user_ids,
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


@router.post("/{comment_id}/like")
async def like_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Like a comment.
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

    # Increment like count
    comment.like_count += 1
    db.commit()

    return {
        "code": 0,
        "message": "点赞成功",
        "data": {
            "like_count": comment.like_count,
        },
    }


@router.delete("/{comment_id}/like")
async def unlike_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Unlike a comment (decrement like count).
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

    # Decrement like count (minimum 0)
    comment.like_count = max(0, comment.like_count - 1)
    db.commit()

    return {
        "code": 0,
        "message": "取消点赞成功",
        "data": {
            "like_count": comment.like_count,
        },
    }


@router.get("/mentions/me")
async def get_my_mentions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get comments where current user was mentioned.
    """
    # Find comments where user_id is in mention_user_ids
    query = db.query(Comment).filter(
        Comment.is_deleted == 0,
        Comment.status == 1,
        Comment.mention_user_ids.isnot(None),
    ).order_by(Comment.create_time.desc())

    # Filter by current user in mention list
    all_mentions = query.all()
    user_mentions = [
        c for c in all_mentions
        if current_user.user_id in c.mention_user_ids.split(",")
    ]

    total = len(user_mentions)
    offset = (page - 1) * page_size
    paginated = user_mentions[offset:offset + page_size]

    result = []
    for c in paginated:
        # Parse mentions
        mention_usernames = parse_mentions(c.content)
        mention_users = get_mentioned_users(mention_usernames, db)

        result.append({
            "comment_id": c.comment_id,
            "project_id": c.project_id,
            "material_id": c.material_id,
            "user_id": c.user_id,
            "user_name": c.user.real_name if c.user else "未知",
            "content": c.content,
            "parent_id": c.parent_id,
            "like_count": c.like_count,
            "reply_count": c.reply_count,
            "mention_users": mention_users,
            "create_time": c.create_time.isoformat() if c.create_time else None,
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


@router.get("/users/search")
async def search_users(
    keyword: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search users by username or real_name for @mention.
    """
    users = db.query(User).filter(
        User.status == 1,
        (User.username.like(f"%{keyword}%")) | (User.real_name.like(f"%{keyword}%")),
    ).limit(10).all()

    return {
        "code": 0,
        "data": [
            {
                "user_id": u.user_id,
                "username": u.username,
                "real_name": u.real_name,
            }
            for u in users
        ],
    }