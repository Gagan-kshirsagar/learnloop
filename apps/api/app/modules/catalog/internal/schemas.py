from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── Lesson Schemas ──


class LessonCreateRequest(BaseModel):
    module_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    content_md: str = Field(default="")
    position: int | None = None


class LessonUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    content_md: str | None = None
    position: int | None = None


class LessonReorderRequest(BaseModel):
    module_id: UUID
    ordered_lesson_ids: list[UUID]


class LessonSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    module_id: UUID
    title: str
    position: int
    created_at: datetime
    updated_at: datetime


class LessonDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    module_id: UUID
    title: str
    content_md: str
    position: int
    created_at: datetime
    updated_at: datetime


class LessonResponse(LessonDetailResponse):
    pass


# ── Module Schemas ──


class ModuleCreateRequest(BaseModel):
    course_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    position: int | None = None


class ModuleUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    position: int | None = None


class ModuleReorderRequest(BaseModel):
    course_id: UUID
    ordered_module_ids: list[UUID]


class ModuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    course_id: UUID
    title: str
    position: int
    created_at: datetime


class ModuleDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    course_id: UUID
    title: str
    position: int
    created_at: datetime
    lessons: list[LessonSummaryResponse] = []


# ── Course Schemas ──


class CourseCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    slug: str | None = Field(None, max_length=255)
    description: str | None = None
    status: str = Field(default="draft")


class CourseUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, max_length=255)
    description: str | None = None
    status: str | None = None


class CourseStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(draft|published)$")


class CourseSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    title: str
    slug: str
    description: str | None
    status: str
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    module_count: int = 0
    lesson_count: int = 0


class CourseDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    title: str
    slug: str
    description: str | None
    status: str
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    modules: list[ModuleDetailResponse] = []


class CourseResponse(CourseDetailResponse):
    pass
