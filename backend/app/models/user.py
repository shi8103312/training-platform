"""
User Model
"""
from sqlalchemy import Column, String, VARCHAR, DATETIME, ForeignKey, Text, BigInteger
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class User(Base):
    """
    User model for both HR admins and employees.
    """
    __tablename__ = "sys_user"

    user_id = Column(VARCHAR(32), primary_key=True, comment="User ID (Employee ID)")
    dept_id = Column(
        VARCHAR(32), ForeignKey("sys_department.dept_id"), nullable=False, comment="Department ID"
    )
    username = Column(VARCHAR(50), unique=True, nullable=False, comment="Username")
    password_hash = Column(VARCHAR(255), nullable=False, comment="Password hash (bcrypt)")
    real_name = Column(VARCHAR(50), nullable=False, comment="Real name")
    email = Column(VARCHAR(100), unique=True, nullable=False, comment="Email")
    phone = Column(VARCHAR(20), nullable=True, comment="Phone number")
    role = Column(TINYINT, nullable=False, default=2, comment="Role: 1=HR_ADMIN, 2=EMPLOYEE")
    avatar = Column(VARCHAR(255), nullable=True, comment="Avatar URL")
    status = Column(TINYINT, nullable=False, default=1, comment="Status: 0=Disabled, 1=Enabled")
    last_login_time = Column(DATETIME, nullable=True, comment="Last login time")
    last_login_ip = Column(VARCHAR(50), nullable=True, comment="Last login IP")
    create_time = Column(DATETIME, nullable=False, server_default=func.now())
    update_time = Column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    department = relationship("Department", back_populates="users")
    auth_tokens = relationship("AuthToken", back_populates="user", cascade="all, delete-orphan")
    watch_progress = relationship("WatchProgress", back_populates="user")
    exam_attempts = relationship("ExamAttempt", back_populates="user")
    comments = relationship("Comment", back_populates="user")

    @property
    def is_hr_admin(self) -> bool:
        return self.role == 1

    @property
    def is_employee(self) -> bool:
        return self.role == 2


class AuthToken(Base):
    """
    Authentication token storage.
    """
    __tablename__ = "sys_auth_token"

    token_id = Column(VARCHAR(64), primary_key=True, comment="Token ID")
    user_id = Column(
        VARCHAR(32), ForeignKey("sys_user.user_id"), nullable=False, comment="User ID"
    )
    token = Column(VARCHAR(500), nullable=False, comment="JWT Token")
    refresh_token = Column(VARCHAR(500), nullable=True, comment="Refresh Token")
    device_info = Column(VARCHAR(255), nullable=True, comment="Device info")
    ip_address = Column(VARCHAR(50), nullable=True, comment="IP Address")
    expires_at = Column(DATETIME, nullable=False, comment="Expiration time")
    create_time = Column(DATETIME, nullable=False, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="auth_tokens")


class AuditLog(Base):
    """
    Audit log for tracking user actions.
    """
    __tablename__ = "sys_audit_log"

    log_id = Column(BigInteger, primary_key=True, autoincrement=True, comment="Log ID")
    user_id = Column(VARCHAR(32), nullable=True, comment="User ID")
    username = Column(VARCHAR(50), nullable=True, comment="Username")
    action = Column(VARCHAR(100), nullable=False, comment="Action type")
    resource_type = Column(VARCHAR(50), nullable=True, comment="Resource type")
    resource_id = Column(VARCHAR(32), nullable=True, comment="Resource ID")
    detail = Column(Text, nullable=True, comment="Operation details (JSON)")
    ip_address = Column(VARCHAR(50), nullable=True, comment="IP Address")
    user_agent = Column(VARCHAR(255), nullable=True, comment="User-Agent")
    create_time = Column(DATETIME, nullable=False, server_default=func.now())