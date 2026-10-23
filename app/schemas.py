from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class LabStatusEnum(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


# ============ User ============
class UserCreate(BaseModel):
    telegram_id: int
    username: Optional[str] = None


class UserOut(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Exam ============
class ExamCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    topic: str = Field(..., min_length=1, max_length=500)
    date: Optional[datetime] = None
    description: Optional[str] = None


class ExamOut(BaseModel):
    id: int
    user_id: int
    subject: str
    topic: str
    date: Optional[datetime]
    description: Optional[str]
    progress: float
    is_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ExamUpdate(BaseModel):
    subject: Optional[str] = None
    topic: Optional[str] = None
    date: Optional[datetime] = None
    description: Optional[str] = None
    progress: Optional[float] = None
    is_completed: Optional[bool] = None


# ============ Exam Topic ============
class ExamTopicCreate(BaseModel):
    exam_id: int
    topic_name: str = Field(..., min_length=1, max_length=500)


class ExamTopicOut(BaseModel):
    id: int
    exam_id: int
    topic_name: str
    is_ready: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Lab Work ============
class LabWorkCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    lab_number: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=500)
    deadline: Optional[datetime] = None
    description: Optional[str] = None


class LabWorkOut(BaseModel):
    id: int
    user_id: int
    subject: str
    lab_number: int
    title: str
    deadline: Optional[datetime]
    status: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class LabWorkUpdate(BaseModel):
    subject: Optional[str] = None
    lab_number: Optional[int] = None
    title: Optional[str] = None
    deadline: Optional[datetime] = None
    status: Optional[LabStatusEnum] = None
    description: Optional[str] = None


# ============ Test ============
class TestCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    title: str = Field(..., min_length=1, max_length=500)


class TestOut(BaseModel):
    id: int
    user_id: int
    subject: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Question ============
class QuestionCreate(BaseModel):
    test_id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_answer: str = Field(..., pattern="^[abcd]$")


class QuestionOut(BaseModel):
    id: int
    test_id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: Optional[str]
    option_d: Optional[str]
    correct_answer: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Test Result ============
class TestResultOut(BaseModel):
    id: int
    user_id: int
    test_id: Optional[int]
    question_id: Optional[int]
    selected_answer: str
    is_correct: bool
    created_at: datetime

    class Config:
        from_attributes = True
