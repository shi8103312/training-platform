"""
Training Models - Project, Material, Progress
"""
from sqlalchemy import (
    Column,
    String,
    VARCHAR,
    DATETIME,
    TEXT,
    ForeignKey,
    JSON,
    INT,
    BigInteger,
)
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Project(Base):
    """
    Training project model.
    """
    __tablename__ = "tra_project"

    project_id = Column(VARCHAR(32), primary_key=True, comment="Project ID")
    title = Column(VARCHAR(200), nullable=False, comment="Project title")
    description = Column(TEXT, nullable=True, comment="Project description")
    cover_image = Column(VARCHAR(255), nullable=True, comment="Cover image URL")
    status = Column(
        TINYINT, nullable=False, default=0, comment="Status: 0=Draft, 1=Published, 2=Unpublished, 3=Ended"
    )
    is_required = Column(
        TINYINT, nullable=False, default=1, comment="Is required: 0=Optional, 1=Required"
    )
    push_scope = Column(JSON, nullable=False, comment="Push scope configuration")
    deadline = Column(DATETIME, nullable=False, comment="Deadline")
    created_by = Column(
        VARCHAR(32), ForeignKey("sys_user.user_id"), nullable=False, comment="Creator ID"
    )
    published_at = Column(DATETIME, nullable=True, comment="Published at")
    create_time = Column(DATETIME, nullable=False, server_default=func.now())
    update_time = Column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    is_deleted = Column(
        TINYINT, nullable=False, default=0, comment="Soft delete: 0=Not deleted, 1=Deleted"
    )

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    materials = relationship("Material", back_populates="project", cascade="all, delete-orphan")
    exams = relationship("Exam", back_populates="project", cascade="all, delete-orphan")
    progress_records = relationship("Progress", back_populates="project")
    comments = relationship("Comment", back_populates="project")

    @property
    def status_text(self) -> str:
        status_map = {0: "草稿", 1: "已发布", 2: "已下架", 3: "已结束"}
        return status_map.get(self.status, "未知")

    @property
    def is_published(self) -> bool:
        return self.status == 1


class Material(Base):
    """
    Training material model (video or document).
    """
    __tablename__ = "tra_material"

    material_id = Column(VARCHAR(32), primary_key=True, comment="Material ID")
    project_id = Column(
        VARCHAR(32), ForeignKey("tra_project.project_id"), nullable=False, comment="Project ID"
    )
    title = Column(VARCHAR(200), nullable=False, comment="Material title")
    material_type = Column(TINYINT, nullable=False, comment="Type: 1=Video, 2=Document")
    storage_path = Column(VARCHAR(500), nullable=False, comment="Storage path (OSS key)")
    preview_path = Column(VARCHAR(500), nullable=True, comment="Preview path")
    thumbnail_path = Column(VARCHAR(255), nullable=True, comment="Thumbnail path")
    duration = Column(INT, nullable=True, comment="Duration in seconds (for video)")
    file_size = Column(BigInteger, nullable=False, comment="File size in bytes")
    file_extension = Column(VARCHAR(20), nullable=False, comment="File extension")
    mime_type = Column(VARCHAR(100), nullable=False, comment="MIME type")
    encryption_key = Column(VARCHAR(64), nullable=True, comment="Video encryption key")
    sort_order = Column(INT, nullable=False, default=0, comment="Sort order")
    status = Column(TINYINT, nullable=False, default=1, comment="Status: 0=Disabled, 1=Enabled")
    create_time = Column(DATETIME, nullable=False, server_default=func.now())
    update_time = Column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    is_deleted = Column(
        TINYINT, nullable=False, default=0, comment="Soft delete"
    )

    # Relationships
    project = relationship("Project", back_populates="materials")
    watch_progress = relationship("WatchProgress", back_populates="material")

    @property
    def is_video(self) -> bool:
        return self.material_type == 1

    @property
    def is_document(self) -> bool:
        return self.material_type == 2


class WatchProgress(Base):
    """
    Individual material watch progress.
    """
    __tablename__ = "tra_watch_progress"

    record_id = Column(VARCHAR(32), primary_key=True, comment="Record ID")
    user_id = Column(
        VARCHAR(32), ForeignKey("sys_user.user_id"), nullable=False, comment="User ID"
    )
    material_id = Column(
        VARCHAR(32), ForeignKey("tra_material.material_id"), nullable=False, comment="Material ID"
    )
    watched_seconds = Column(INT, nullable=False, default=0, comment="Watched seconds (current position)")
    max_position = Column(INT, nullable=False, default=0, comment="Maximum position reached")
    total_duration = Column(INT, nullable=False, default=0, comment="Total material duration")
    total_watched_seconds = Column(INT, nullable=False, default=0, comment="Total accumulated watch time")
    is_completed = Column(
        TINYINT, nullable=False, default=0, comment="Is completed: 0=Not completed, 1=Completed"
    )
    completed_at = Column(DATETIME, nullable=True, comment="Completed at")
    last_watch_time = Column(DATETIME, nullable=False, comment="Last watch time")
    create_time = Column(DATETIME, nullable=False, server_default=func.now())
    update_time = Column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    user = relationship("User", back_populates="watch_progress")
    material = relationship("Material", back_populates="watch_progress")

    @property
    def progress_percentage(self) -> int:
        # Use total_duration if set, don't access material relationship to avoid lazy load issues
        duration = self.total_duration
        if duration == 0:
            # Fallback: use max_position directly as percentage (max 100)
            # This happens for videos uploaded before duration extraction was implemented
            return min(self.max_position, 100)
        return int((self.max_position / duration) * 100)


class Progress(Base):
    """
    Overall project progress for a user.
    """
    __tablename__ = "tra_progress"

    progress_id = Column(VARCHAR(32), primary_key=True, comment="Progress ID")
    user_id = Column(
        VARCHAR(32), ForeignKey("sys_user.user_id"), nullable=False, comment="User ID"
    )
    project_id = Column(
        VARCHAR(32), ForeignKey("tra_project.project_id"), nullable=False, comment="Project ID"
    )
    material_progress = Column(JSON, nullable=False, comment="Material progress details")
    exam_attempt_id = Column(
        VARCHAR(32), nullable=True, comment="Related exam attempt ID"
    )
    overall_status = Column(
        TINYINT, nullable=False, default=0, comment="Overall status: 0=Not started, 1=In progress, 2=Completed"
    )
    start_time = Column(DATETIME, nullable=True, comment="Start time")
    completion_time = Column(DATETIME, nullable=True, comment="Completion time")
    total_time_spent = Column(INT, nullable=False, default=0, comment="Total time spent in seconds")
    create_time = Column(DATETIME, nullable=False, server_default=func.now())
    update_time = Column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    project = relationship("Project", back_populates="progress_records")

    @property
    def status_text(self) -> str:
        status_map = {0: "未开始", 1: "进行中", 2: "已完成"}
        return status_map.get(self.overall_status, "未知")


class Comment(Base):
    """
    Project and material comments.
    """
    __tablename__ = "tra_comment"

    comment_id = Column(VARCHAR(32), primary_key=True, comment="Comment ID")
    project_id = Column(
        VARCHAR(32), ForeignKey("tra_project.project_id"), nullable=False, comment="Project ID"
    )
    material_id = Column(
        VARCHAR(32), ForeignKey("tra_material.material_id"), nullable=True, comment="Material ID"
    )
    user_id = Column(
        VARCHAR(32), ForeignKey("sys_user.user_id"), nullable=False, comment="User ID"
    )
    content = Column(TEXT, nullable=False, comment="Comment content")
    parent_id = Column(VARCHAR(32), nullable=True, comment="Parent comment ID (for replies)")
    like_count = Column(INT, nullable=False, default=0, comment="Like count")
    reply_count = Column(INT, nullable=False, default=0, comment="Reply count")
    status = Column(TINYINT, nullable=False, default=1, comment="Status: 0=Hidden, 1=Visible")
    mention_user_ids = Column(VARCHAR(500), nullable=True, comment="Mentioned user IDs, comma separated")
    is_deleted = Column(
        TINYINT, nullable=False, default=0, comment="Soft delete"
    )
    create_time = Column(DATETIME, nullable=False, server_default=func.now())
    update_time = Column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    project = relationship("Project", back_populates="comments")
    material = relationship("Material", foreign_keys=[material_id])
    user = relationship("User", back_populates="comments")
    parent = relationship(
        "Comment",
        remote_side=[comment_id],
        primaryjoin="Comment.comment_id == foreign(Comment.parent_id)",
        backref="replies",
        viewonly=True
    )