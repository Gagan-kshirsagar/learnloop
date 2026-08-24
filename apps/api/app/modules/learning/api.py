from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.identity.api import (
    UserResponse,
    get_current_user,
    get_tenant_db_session,
    require_role,
)
from app.modules.learning.internal.schemas import (
    EnrollmentResponse,
    ExerciseCreateUpdateRequest,
    ExerciseDetailResponse,
    ExerciseResponse,
    LessonCompleteRequest,
    MyEnrollmentSummary,
    ProgressResponse,
    SubmissionQueuedResponse,
    SubmissionStatusResponse,
    SubmitCodeRequest,
)
from app.modules.learning.internal.service import LearningService
from app.shared.db import get_session_factory

router = APIRouter(prefix="/learning", tags=["learning"])


def get_learning_service(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> LearningService:
    return LearningService(session_factory=session_factory)


# ── Enrollment Endpoints ──


@router.post(
    "/courses/{course_id}/enroll",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_in_course(
    course_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    service: LearningService = Depends(get_learning_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> EnrollmentResponse:
    return await service.enroll(
        session,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        course_id=course_id,
    )


@router.get("/me/enrollments", response_model=list[MyEnrollmentSummary])
async def list_my_enrollments(
    current_user: UserResponse = Depends(get_current_user),
    service: LearningService = Depends(get_learning_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> list[MyEnrollmentSummary]:
    return await service.list_my_enrollments(
        session,
        user_id=current_user.id,
    )


# ── Exercise Endpoints (Learner & Author) ──


@router.get("/lessons/{lesson_id}/exercise", response_model=ExerciseResponse | None)
async def get_exercise_for_lesson(
    lesson_id: UUID,
    _current_user: UserResponse = Depends(get_current_user),
    service: LearningService = Depends(get_learning_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> ExerciseResponse | None:
    return await service.get_exercise_for_learner(session, lesson_id=lesson_id)


@router.get(
    "/lessons/{lesson_id}/exercise/author",
    response_model=ExerciseDetailResponse,
    dependencies=[Depends(require_role("owner", "instructor"))],
)
async def get_exercise_for_author(
    lesson_id: UUID,
    _current_user: UserResponse = Depends(get_current_user),
    service: LearningService = Depends(get_learning_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> ExerciseDetailResponse:
    return await service.get_exercise_for_author(session, lesson_id=lesson_id)


@router.post(
    "/lessons/{lesson_id}/exercise",
    response_model=ExerciseDetailResponse,
    dependencies=[Depends(require_role("owner", "instructor"))],
)
async def save_exercise(
    lesson_id: UUID,
    req: ExerciseCreateUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    service: LearningService = Depends(get_learning_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> ExerciseDetailResponse:
    return await service.save_exercise_author(
        session,
        tenant_id=current_user.tenant_id,
        lesson_id=lesson_id,
        req=req,
    )


# ── Code Submission Endpoints ──


@router.post("/exercises/{exercise_id}/submit", response_model=SubmissionQueuedResponse)
async def submit_exercise_code(
    exercise_id: UUID,
    req: SubmitCodeRequest,
    current_user: UserResponse = Depends(get_current_user),
    service: LearningService = Depends(get_learning_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> SubmissionQueuedResponse:
    return await service.submit_code(
        session,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        user_role=current_user.role,
        exercise_id=exercise_id,
        req=req,
    )


@router.get("/submissions/{submission_id}", response_model=SubmissionStatusResponse)
async def get_submission_status(
    submission_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    service: LearningService = Depends(get_learning_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> SubmissionStatusResponse:
    return await service.get_submission_status(
        session,
        submission_id=submission_id,
        user_id=current_user.id,
        user_role=current_user.role,
    )


# ── Progress Completion ──


@router.post("/lessons/{lesson_id}/complete", response_model=ProgressResponse)
async def complete_lesson(
    lesson_id: UUID,
    req: LessonCompleteRequest,
    current_user: UserResponse = Depends(get_current_user),
    service: LearningService = Depends(get_learning_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> ProgressResponse:
    return await service.complete_lesson(
        session,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        lesson_id=lesson_id,
        completed=req.completed,
    )


__all__ = [
    "router",
    "EnrollmentResponse",
    "MyEnrollmentSummary",
    "ExerciseResponse",
    "ExerciseDetailResponse",
    "SubmissionQueuedResponse",
    "SubmissionStatusResponse",
    "ProgressResponse",
]
