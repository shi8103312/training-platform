"""
Notification API Routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
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