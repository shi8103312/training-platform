"""
Training Project and Material Schemas
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Union
from datetime import datetime, timezone


# ============ Project Schemas ============

class PushScope(BaseModel):
    type: str = Field(..., description="Scope type: all, departments, users")
    departments: Optional[List[str]] = Field(default=None)
    users: Optional[List[str]] = Field(default=None)

    @model_validator(mode="after")
    def check_scope(self):
        if self.type == "departments" and not self.departments:
            raise ValueError("选择部门范围时必须指定部门列表")
        if self.type == "users" and not self.users:
            raise ValueError("选择用户范围时必须指定用户列表")
        return self


class CreateProjectRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    cover_image: Optional[str] = None
    deadline: datetime
    is_required: bool = True
    push_scope: PushScope

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        import re
        if not re.match(r'^[\w一-龥]+$', v):
            raise ValueError("项目名称只能包含字母、数字、中文和下划线")
        return v.strip()

    @field_validator("deadline")
    @classmethod
    def validate_deadline(cls, v):
        now = datetime.now(timezone.utc)
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v <= now:
            raise ValueError("截止日期必须晚于当前时间")
        return v


class UpdateProjectRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    cover_image: Optional[str] = None
    deadline: Optional[datetime] = None
    is_required: Optional[bool] = None
    push_scope: Optional[PushScope] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if v is None:
            return v
        import re
        if not re.match(r'^[\w一-龥]+$', v):
            raise ValueError("项目名称只能包含字母、数字、中文和下划线")
        return v.strip()


class ProjectResponse(BaseModel):
    project_id: str
    title: str
    description: Optional[str] = None
    cover_image: Optional[str] = None
    status: int
    status_text: str
    is_required: bool
    deadline: datetime
    created_by: str
    published_at: Optional[datetime] = None
    create_time: datetime

    class Config:
        from_attributes = True


class ProjectDetailResponse(BaseModel):
    project_id: str
    title: str
    description: Optional[str] = None
    cover_image: Optional[str] = None
    status: int
    status_text: str
    is_required: bool
    push_scope: dict
    deadline: datetime
    created_by: str
    creator_name: Optional[str] = None
    published_at: Optional[datetime] = None
    create_time: datetime
    materials: List["MaterialResponse"] = []
    exam: Optional["ExamBasicResponse"] = None

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    code: int = 0
    data: dict


# ============ Material Schemas ============

class UploadMaterialRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=100)
    material_type: int = Field(..., ge=1, le=2)
    sort_order: Optional[int] = Field(default=0, ge=0)


class MaterialResponse(BaseModel):
    material_id: str
    project_id: str
    title: str
    material_type: int
    material_type_text: str
    duration: Optional[int] = None
    file_size: int
    thumbnail: Optional[str] = None
    sort_order: int
    status: int
    create_time: datetime

    class Config:
        from_attributes = True


class MaterialUploadResponse(BaseModel):
    material_id: str
    title: str
    material_type: int
    duration: Optional[int] = None
    thumbnail: Optional[str] = None
    file_size: int
    status: str


class PlayTokenResponse(BaseModel):
    play_url: str
    token: str
    token_expires_at: datetime


# ============ Progress Schemas ============

class UpdateProgressRequest(BaseModel):
    material_id: str = Field(..., min_length=1)
    play_position: int = Field(..., ge=0)
    max_position: int = Field(..., ge=0)
    total_watched_seconds: Optional[int] = Field(default=0, ge=0)

    @model_validator(mode="after")
    def check_positions(self):
        if self.play_position < 0 or self.max_position < 0:
            raise ValueError("进度位置不能为负数")
        return self


class MaterialProgressResponse(BaseModel):
    material_id: str
    title: str
    material_type: int
    progress: int
    max_position: int
    is_completed: bool
    is_required: bool = True


class ExamStatusResponse(BaseModel):
    exam_id: str
    attempt_id: Optional[str] = None
    status: Optional[str] = None
    score: Optional[int] = None


class ProgressResponse(BaseModel):
    project_id: str
    overall_status: int
    overall_status_text: str
    materials: List[MaterialProgressResponse]
    exam: Optional[ExamStatusResponse] = None


# ============ Exam Schemas ============

class QuestionOption(BaseModel):
    key: str
    text: str


class QuestionSchema(BaseModel):
    question_type: int = Field(..., ge=1, le=4)
    question_text: str = Field(..., min_length=1)
    options: Optional[List[QuestionOption]] = None
    correct_answer: str = Field(..., min_length=1)
    score: int = Field(default=5, ge=1)
    explanation: Optional[str] = None


class CreateExamRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    passing_score: int = Field(default=60, ge=0, le=100)
    duration_minutes: int = Field(..., ge=1)
    attempt_limit: int = Field(default=1, ge=1)
    random_shuffle: bool = False
    show_answer: bool = False
    questions: List[QuestionSchema] = Field(..., min_length=1)


class ExamBasicResponse(BaseModel):
    exam_id: str
    title: str

    class Config:
        from_attributes = True


class ExamDetailResponse(BaseModel):
    exam_id: str
    project_id: str
    title: str
    description: Optional[str] = None
    passing_score: int
    duration_minutes: int
    attempt_limit: int
    total_score: int
    question_count: int
    status: int

    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    question_id: str
    question_type: int
    question_type_text: str
    question_text: str
    options: Optional[List[QuestionOption]] = None
    score: int

    class Config:
        from_attributes = True


class ExamStartResponse(BaseModel):
    attempt_id: str
    start_time: datetime
    deadline: datetime
    questions: List[QuestionResponse]


class AnswerItem(BaseModel):
    question_id: str
    answer: Union[str, List[str]]


class SaveAnswerRequest(BaseModel):
    answers: List[AnswerItem]


class AnswerResult(BaseModel):
    question_id: str
    your_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    correct: bool


class ExamSubmitResponse(BaseModel):
    attempt_id: str
    score: int
    passed: bool
    correct_count: int
    total_count: int
    submit_time: datetime
    time_spent: int
    answers: List[AnswerResult]


class ExamHistoryItem(BaseModel):
    attempt_id: str
    exam_id: str
    exam_title: str
    start_time: datetime
    submit_time: Optional[datetime] = None
    score: Optional[int] = None
    passed: Optional[bool] = None
    status: str


class ExamHistoryResponse(BaseModel):
    code: int = 0
    data: List[ExamHistoryItem]


# ============ Comment Schemas ============

class CreateCommentRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    material_id: Optional[str] = None
    content: str = Field(..., min_length=1, max_length=500)
    parent_id: Optional[str] = None


class CommentResponse(BaseModel):
    comment_id: str
    project_id: str
    material_id: Optional[str] = None
    user_id: str
    user_name: str
    content: str
    parent_id: Optional[str] = None
    like_count: int
    reply_count: int
    mention_users: List[dict] = []
    create_time: datetime
    replies: List["CommentResponse"] = []

    class Config:
        from_attributes = True


# ============ Notification Schemas ============

class SendNotificationRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    send_now: bool = True
    schedule_time: Optional[datetime] = None


# Update forward references
CommentResponse.model_rebuild()
ProjectDetailResponse.model_rebuild()