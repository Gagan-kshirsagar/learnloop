from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.api import (
    UserResponse,
    get_current_user,
    get_tenant_db_session,
    require_role,
)
from app.modules.tutor.internal.schemas import (
    AskQuestionRequest,
    AskQuestionResponse,
    CitationResponse,
    CourseIngestResponse,
    LessonIngestResponse,
)
from app.modules.tutor.internal.service import TutorService

router = APIRouter(prefix="/tutor", tags=["tutor"])


def get_tutor_service() -> TutorService:
    return TutorService()


@router.post("/ask", response_model=AskQuestionResponse)
async def ask_tutor(
    req: AskQuestionRequest,
    current_user: UserResponse = Depends(get_current_user),
    service: TutorService = Depends(get_tutor_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> AskQuestionResponse:
    return await service.ask_question(
        session,
        tenant_id=current_user.tenant_id,
        question=req.question,
        lesson_id=req.lesson_id,
    )


@router.post(
    "/lessons/{lesson_id}/ingest",
    response_model=LessonIngestResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("owner", "instructor"))],
)
async def ingest_lesson(
    lesson_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    service: TutorService = Depends(get_tutor_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> LessonIngestResponse:
    return await service.ingest_lesson(
        session,
        tenant_id=current_user.tenant_id,
        lesson_id=lesson_id,
    )


@router.post(
    "/courses/{course_id}/ingest",
    response_model=CourseIngestResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("owner", "instructor"))],
)
async def ingest_course(
    course_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    service: TutorService = Depends(get_tutor_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> CourseIngestResponse:
    return await service.ingest_course(
        session,
        tenant_id=current_user.tenant_id,
        course_id=course_id,
    )


__all__ = [
    "router",
    "AskQuestionRequest",
    "AskQuestionResponse",
    "CitationResponse",
    "LessonIngestResponse",
    "CourseIngestResponse",
]
