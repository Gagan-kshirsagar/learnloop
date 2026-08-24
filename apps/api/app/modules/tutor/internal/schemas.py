from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AskQuestionRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    question: str = Field(..., min_length=2, max_length=1000)
    lesson_id: UUID | None = None


class CitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lesson_id: UUID
    ordinal: int
    snippet: str
    score: float


class AskQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    answer: str
    citations: list[CitationResponse] = Field(default_factory=list)
    used_context: bool


class LessonIngestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lesson_id: UUID
    chunks_created: int
    total_tokens: int


class CourseIngestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_id: UUID
    lessons_ingested: int
    total_chunks: int
