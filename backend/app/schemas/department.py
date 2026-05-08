"""
Department Schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class DepartmentBase(BaseModel):
    dept_id: Optional[str] = None
    dept_code: str = Field(..., min_length=1, max_length=50)
    dept_name: str = Field(..., min_length=1, max_length=100)
    parent_id: Optional[str] = None
    sort_order: int = Field(default=0, ge=0)
    status: int = Field(default=1, ge=0, le=1)

    @field_validator("dept_code")
    @classmethod
    def validate_dept_code(cls, v):
        if not v.replace("_", "").isalnum():
            raise ValueError("部门编码只能包含字母、数字和下划线")
        return v.upper()


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    dept_name: Optional[str] = Field(None, max_length=100)
    parent_id: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)
    status: Optional[int] = Field(None, ge=0, le=1)


class DepartmentResponse(BaseModel):
    dept_id: str
    dept_code: str
    dept_name: str
    parent_id: Optional[str] = None
    dept_level: int
    sort_order: int
    status: int
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class DepartmentTreeResponse(BaseModel):
    dept_id: str
    dept_name: str
    dept_level: int
    children: List["DepartmentTreeResponse"] = []

    class Config:
        from_attributes = True


class ImportDepartmentRequest(BaseModel):
    file_path: str
    mode: str = Field(default="simulate")  # create, update, simulate


class ImportError(BaseModel):
    row: int
    dept_code: str
    error: str


class ImportResultResponse(BaseModel):
    mode: str
    total: int
    success: int
    failed: int
    errors: List[ImportError] = []


class DepartmentListResponse(BaseModel):
    code: int = 0
    data: List[DepartmentResponse]