"""
Notification Model
"""
from sqlalchemy import Column, String, VARCHAR, DATETIME, TEXT, ForeignKey, INT
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Notification(Base):
    """
    Notification log model.
    """
    __tablename__ = "notif_log"

    notif_id = Column(VARCHAR(32), primary_key=True, comment="Notification ID")
    user_id = Column(
        VARCHAR(32), ForeignKey("sys_user.user_id"), nullable=False, comment="Recipient user ID"
    )
    notif_type = Column(
        TINYINT, nullable=False, comment="Notification type: 1=Training notification, 2=Deadline reminder, 3=Exam notification"
    )
    title = Column(VARCHAR(200), nullable=False, comment="Notification title")
    content = Column(TEXT, nullable=False, comment="Notification content")
    project_id = Column(
        VARCHAR(32), ForeignKey("tra_project.project_id"), nullable=True, comment="Related project ID"
    )
    email_status = Column(
        TINYINT, nullable=False, default=0, comment="Email status: 0=Pending, 1=Sent, 2=Failed"
    )
    email_sent_at = Column(DATETIME, nullable=True, comment="Email sent at")
    email_error = Column(VARCHAR(500), nullable=True, comment="Email error message")
    read_status = Column(
        TINYINT, nullable=False, default=0, comment="Read status: 0=Unread, 1=Read"
    )
    read_at = Column(DATETIME, nullable=True, comment="Read at")
    create_time = Column(DATETIME, nullable=False, server_default=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    project = relationship("Project", foreign_keys=[project_id])

    @property
    def notif_type_text(self) -> str:
        type_map = {1: "培训通知", 2: "截止提醒", 3: "考试通知"}
        return type_map.get(self.notif_type, "未知")

    @property
    def email_status_text(self) -> str:
        status_map = {0: "待发送", 1: "已发送", 2: "发送失败"}
        return status_map.get(self.email_status, "未知")