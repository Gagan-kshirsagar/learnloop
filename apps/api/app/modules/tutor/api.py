from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
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
    ChatMessageResponse,
    ChatSessionDetailResponse,
    ChatSessionResponse,
    CitationResponse,
    CourseIngestResponse,
    LessonIngestResponse,
    StreamQuestionRequest,
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


@router.post("/stream")
async def stream_tutor(
    req: StreamQuestionRequest,
    current_user: UserResponse = Depends(get_current_user),
    service: TutorService = Depends(get_tutor_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> StreamingResponse:
    """Stream token-by-token tutor responses using Server-Sent Events (SSE)."""
    return StreamingResponse(
        service.stream_question(
            session=session,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            req=req,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_chat_sessions(
    lesson_id: UUID | None = Query(None),
    current_user: UserResponse = Depends(get_current_user),
    service: TutorService = Depends(get_tutor_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> list[ChatSessionResponse]:
    return await service.list_sessions(
        session=session,
        user_id=current_user.id,
        lesson_id=lesson_id,
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionDetailResponse)
async def get_chat_session_detail(
    session_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    service: TutorService = Depends(get_tutor_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> ChatSessionDetailResponse:
    return await service.get_session_detail(
        session=session,
        user_id=current_user.id,
        session_id=session_id,
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    service: TutorService = Depends(get_tutor_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> None:
    await service.delete_session(
        session=session,
        user_id=current_user.id,
        session_id=session_id,
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
    "StreamQuestionRequest",
    "AskQuestionResponse",
    "CitationResponse",
    "ChatMessageResponse",
    "ChatSessionResponse",
    "ChatSessionDetailResponse",
    "LessonIngestResponse",
    "CourseIngestResponse",
]
