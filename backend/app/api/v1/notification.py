"""
Notification API Routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import uuid
import json

from ...database import get_db
from ...models.user import User
from ...models.training import Project
from ...models.notification import Notification
from ...models.user import User as UserModel
from ...api.deps import get_current_user, require_hr_admin
from ...core.permissions import Role, check_user_access_to_project
from ...schemas.training import SendNotificationRequest

router = APIRouter(prefix="/notification", tags=["通知"])


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get unread notification count (for polling).
    """
    count = db.query(Notification).filter(
        Notification.user_id == current_user.user_id,
        Notification.read_status == 0,
    ).count()

    return {
        "code": 0,
        "data": {
            "count": count,
        },
    }


@router.post("/send")
async def send_notification(
    notif_data: SendNotificationRequest,
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Send training notification to target users.

    Rules:
    - Max 500 recipients per batch
    - Batch size: 100, interval: 5 seconds
    - Rate limit: 100 per minute
    """
    # Get project
    project = db.query(Project).filter(
        Project.project_id == notif_data.project_id,
        Project.is_deleted == 0,
    ).first()

    if not project:
        return {
            "code": 20001,
            "message": "项目不存在",
        }

    # Get target users based on push scope
    push_scope = project.push_scope
    if isinstance(push_scope, str):
        push_scope = json.loads(push_scope)

    scope_type = push_scope.get("type")

    query = db.query(UserModel).filter(UserModel.status == 1)

    if scope_type == "all":
        pass  # All active users
    elif scope_type == "departments":
        dept_ids = push_scope.get("departments", [])
        query = query.filter(UserModel.dept_id.in_(dept_ids))
    elif scope_type == "users":
        user_ids = push_scope.get("users", [])
        query = query.filter(UserModel.user_id.in_(user_ids))
    else:
        return {
            "code": 70002,
            "message": "无有效通知对象",
        }

    users = query.all()

    if not users:
        return {
            "code": 70002,
            "message": "无有效通知对象",
        }

    # Create notification records
    notifications = []
    for u in users:
        notif_id = f"N{uuid.uuid4().hex[:8].upper()}"
        notification = Notification(
            notif_id=notif_id,
            user_id=u.user_id,
            notif_type=1,  # Training notification
            title=f"【培训通知】{project.title}",
            content=_build_notification_content(project),
            project_id=project.project_id,
            email_status=0,  # Pending
        )
        notifications.append(notification)
        db.add(notification)

    db.commit()

    # TODO: Implement actual email sending with rate limiting
    # For now, just mark as pending

    return {
        "code": 0,
        "message": f"通知已创建，共 {len(notifications)} 人",
        "data": {
            "total": len(notifications),
            "pending": len(notifications),
        },
    }


@router.get("/history")
async def get_notification_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Get notification history for HR admin.
    Returns list of notifications sent by the admin.
    """
    # Get notifications created by current user
    query = db.query(Notification).filter(
        Notification.project_id.isnot(None)
    )

    total = query.count()
    offset = (page - 1) * page_size
    notifications = query.order_by(Notification.create_time.desc()).offset(offset).limit(page_size).all()

    # Group by project and send time
    history_map = {}
    for n in notifications:
        key = f"{n.project_id}_{n.create_time.strftime('%Y-%m-%d %H:%M')}"
        if key not in history_map:
            history_map[key] = {
                "id": n.notif_id,
                "title": n.title,
                "project": n.project.title if n.project else "",
                "scope": _get_scope_text(n),
                "send_time": n.create_time.strftime('%Y-%m-%d %H:%M'),
                "count": 0,
                "status": "sent" if n.email_status == 1 else "pending",
                "status_class": "sent" if n.email_status == 1 else "pending",
                "status_text": "已发送" if n.email_status == 1 else "发送中",
            }
        history_map[key]["count"] += 1

    history_list = list(history_map.values())

    return {
        "code": 0,
        "data": history_list,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }


@router.get("/list")
async def get_my_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get notifications for current user (employee).
    """
    query = db.query(Notification).filter(Notification.user_id == current_user.user_id)

    total = query.count()
    offset = (page - 1) * page_size
    notifications = query.order_by(Notification.create_time.desc()).offset(offset).limit(page_size).all()

    return {
        "code": 0,
        "data": [
            {
                "notif_id": n.notif_id,
                "title": n.title,
                "content": n.content,
                "notif_type": n.notif_type,
                "notif_type_text": n.notif_type_text,
                "project_id": n.project_id,
                "project_title": n.project.title if n.project else None,
                "read_status": n.read_status,
                "read_at": n.read_at.isoformat() if n.read_at else None,
                "create_time": n.create_time.isoformat() if n.create_time else None,
            }
            for n in notifications
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }


@router.put("/{notif_id}/read")
async def mark_notification_read(
    notif_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark a notification as read.
    """
    notification = db.query(Notification).filter(
        Notification.notif_id == notif_id,
        Notification.user_id == current_user.user_id,
    ).first()

    if not notification:
        return {
            "code": 40401,
            "message": "通知不存在",
        }

    notification.read_status = 1
    notification.read_at = datetime.now()
    db.commit()

    return {
        "code": 0,
        "message": "已标记为已读",
    }


def _get_scope_text(notification: Notification) -> str:
    """Get scope description for notification."""
    if not notification.project:
        return "未知"
    push_scope = notification.project.push_scope
    if isinstance(push_scope, str):
        push_scope = json.loads(push_scope)
    scope_type = push_scope.get("type") if push_scope else None
    if scope_type == "all":
        return "全员"
    elif scope_type == "departments":
        return "指定部门"
    elif scope_type == "users":
        return "指定人员"
    return "未知"


def _build_notification_content(project: Project) -> str:
    """Build notification email content."""
    return f"""
亲爱的学员：

您有一项新的培训任务等待完成。

培训项目：{project.title}
截止日期：{project.deadline.strftime('%Y-%m-%d %H:%M') if project.deadline else '未设置'}

{"【必修】" if project.is_required else "【选修】"}请在截止日期前完成培训！

此邮件由系统自动发送，请勿回复。
"""


# TODO: Add scheduled task for deadline reminders
# - 3 days before deadline
# - 1 day before deadline
# - On deadline day