"""
Exam Models - Exam, Question, Attempt
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
)
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Exam(Base):
    """
    Exam model.
    """
    __tablename__ = "tra_exam"

    exam_id = Column(VARCHAR(32), primary_key=True, comment="Exam ID")
    project_id = Column(
        VARCHAR(32), ForeignKey("tra_project.project_id"), nullable=False, comment="Project ID"
    )
    title = Column(VARCHAR(200), nullable=False, comment="Exam title")
    description = Column(TEXT, nullable=True, comment="Exam description")
    passing_score = Column(INT, nullable=False, default=60, comment="Passing score")
    duration_minutes = Column(INT, nullable=False, default=60, comment="Duration in minutes")
    attempt_limit = Column(INT, nullable=False, default=1, comment="Allowed attempts")
    random_shuffle = Column(
        TINYINT, nullable=False, default=0, comment="Random shuffle: 0=No, 1=Yes"
    )
    show_answer = Column(
        TINYINT, nullable=False, default=0, comment="Show answer after exam: 0=No, 1=Yes"
    )
    total_score = Column(INT, nullable=False, default=100, comment="Total score")
    question_count = Column(INT, nullable=False, default=0, comment="Question count")
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
    project = relationship("Project", back_populates="exams")
    questions = relationship(
        "Question", back_populates="exam", cascade="all, delete-orphan"
    )
    attempts = relationship("ExamAttempt", back_populates="exam", cascade="all, delete-orphan")


class Question(Base):
    """
    Exam question model.
    """
    __tablename__ = "tra_question"

    question_id = Column(VARCHAR(32), primary_key=True, comment="Question ID")
    exam_id = Column(
        VARCHAR(32), ForeignKey("tra_exam.exam_id"), nullable=False, comment="Exam ID"
    )
    question_type = Column(
        TINYINT, nullable=False, comment="Question type: 1=Single choice, 2=Multiple choice, 3=True/False, 4=Essay"
    )
    question_text = Column(TEXT, nullable=False, comment="Question text")
    options = Column(JSON, nullable=True, comment="Options JSON: [{key: 'A', text: '...'}]")
    correct_answer = Column(VARCHAR(500), nullable=False, comment="Correct answer")
    score = Column(INT, nullable=False, default=5, comment="Score for this question")
    explanation = Column(TEXT, nullable=True, comment="Answer explanation")
    sort_order = Column(INT, nullable=False, default=0, comment="Sort order")
    create_time = Column(DATETIME, nullable=False, server_default=func.now())
    update_time = Column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    exam = relationship("Exam", back_populates="questions")

    @property
    def question_type_text(self) -> str:
        type_map = {1: "单选题", 2: "多选题", 3: "判断题", 4: "简答题"}
        return type_map.get(self.question_type, "未知")

    @property
    def is_single_choice(self) -> bool:
        return self.question_type == 1

    @property
    def is_multiple_choice(self) -> bool:
        return self.question_type == 2

    @property
    def is_true_false(self) -> bool:
        return self.question_type == 3

    @property
    def is_essay(self) -> bool:
        return self.question_type == 4


class ExamAttempt(Base):
    """
    Exam attempt/record model.
    """
    __tablename__ = "tra_attempt"

    attempt_id = Column(VARCHAR(32), primary_key=True, comment="Attempt ID")
    exam_id = Column(
        VARCHAR(32), ForeignKey("tra_exam.exam_id"), nullable=False, comment="Exam ID"
    )
    user_id = Column(
        VARCHAR(32), ForeignKey("sys_user.user_id"), nullable=False, comment="User ID"
    )
    start_time = Column(DATETIME, nullable=False, comment="Start time")
    submit_time = Column(DATETIME, nullable=True, comment="Submit time")
    time_spent = Column(INT, nullable=True, comment="Time spent in seconds")
    score = Column(INT, nullable=True, comment="Score achieved")
    passed = Column(TINYINT, nullable=True, comment="Passed: 0=Failed, 1=Passed")
    answers = Column(JSON, nullable=True, comment="Answer details: [{question_id, answer, correct}]")
    status = Column(
        TINYINT, nullable=False, default=0, comment="Status: 0=In progress, 1=Submitted, 2=Auto submitted due to timeout"
    )
    create_time = Column(DATETIME, nullable=False, server_default=func.now())

    # Relationships
    exam = relationship("Exam", back_populates="attempts")
    user = relationship("User", back_populates="exam_attempts")

    @property
    def status_text(self) -> str:
        status_map = {0: "进行中", 1: "已提交", 2: "超时自动提交"}
        return status_map.get(self.status, "未知")

    @property
    def is_in_progress(self) -> bool:
        return self.status == 0

    @property
    def is_submitted(self) -> bool:
        return self.status in (1, 2)