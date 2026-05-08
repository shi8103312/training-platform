"""
Department Model
"""
from sqlalchemy import Column, String, VARCHAR, DATETIME, ForeignKey, INT
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Department(Base):
    """
    Department model for organizational hierarchy.
    """
    __tablename__ = "sys_department"

    dept_id = Column(VARCHAR(32), primary_key=True, comment="Department ID")
    parent_id = Column(
        VARCHAR(32), ForeignKey("sys_department.dept_id"), nullable=True, comment="Parent department ID"
    )
    dept_code = Column(VARCHAR(50), unique=True, nullable=False, comment="Department code")
    dept_name = Column(VARCHAR(100), nullable=False, comment="Department name")
    dept_level = Column(TINYINT, nullable=False, default=1, comment="Department level: 1=root")
    sort_order = Column(INT, nullable=False, default=0, comment="Sort order")
    status = Column(TINYINT, nullable=False, default=1, comment="Status: 0=Disabled, 1=Enabled")
    create_time = Column(DATETIME, nullable=False, server_default=func.now())
    update_time = Column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    parent = relationship("Department", remote_side=[dept_id], back_populates="children")
    children = relationship("Department", back_populates="parent", cascade="all, delete-orphan")
    users = relationship("User", back_populates="department")

    def get_all_children(self) -> list:
        """
        Get all descendant departments recursively.
        """
        result = []
        for child in self.children:
            result.append(child)
            result.extend(child.get_all_children())
        return result

    def get_dept_path(self) -> str:
        """
        Get full department path like '集团/技术部/前端组'.
        """
        path_parts = [self.dept_name]
        current = self.parent
        while current:
            path_parts.insert(0, current.dept_name)
            current = current.parent
        return "/".join(path_parts)