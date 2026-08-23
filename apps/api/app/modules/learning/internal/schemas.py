from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── Enrollment Schemas ──


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID
    course_id: UUID
    status: str
    enrolled_at: datetime


class MyEnrollmentSummary(BaseModel):
    id: UUID
    course_id: UUID
    course_title: str
    course_slug: str
    course_description: str | None = None
    status: str
    enrolled_at: datetime
    total_lessons: int = 0
    completed_lessons: int = 0
    progress_percentage: int = 0


# ── Exercise Schemas ──


class ExerciseResponse(BaseModel):
    """Safe learner representation - hidden tests_code is omitted."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    lesson_id: UUID
    prompt_md: str
    starter_code: str
    language: str
    created_at: datetime


class ExerciseDetailResponse(ExerciseResponse):
    """Author/Instructor representation - includes hidden tests_code."""

    tests_code: str


class ExerciseCreateUpdateRequest(BaseModel):
    prompt_md: str = Field(default="")
    starter_code: str = Field(default="")
    tests_code: str = Field(default="")
    language: str = Field(default="python")


# ── Submission Schemas ──


class SubmitCodeRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=65536)


class SubmissionQueuedResponse(BaseModel):
    submission_id: UUID
    status: str = "queued"


class SubmissionStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID
    exercise_id: UUID
    status: str
    stdout: str | None = None
    stderr: str | None = None
    tests_passed: int
    tests_total: int
    duration_ms: int | None = None
    created_at: datetime


# ── Progress Schemas ──


class LessonCompleteRequest(BaseModel):
    completed: bool = True


class ProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID
    lesson_id: UUID | None = None
    exercise_id: UUID | None = None
    completed: bool
    attempts: int
    updated_at: datetime
