from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.identity.api import (
    UserResponse,
    get_current_user,
    get_tenant_db_session,
    require_role,
)
from app.modules.learning.internal.models import Exercise, Submission
from app.modules.learning.internal.repository import (
    ExerciseRepository,
    ProgressRepository,
    SubmissionRepository,
)
from app.modules.learning.internal.runner import SubprocessPythonRunner
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
async def save_or_update_exercise(
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


@router.post(
    "/exercises/{exercise_id}/submit",
    response_model=SubmissionQueuedResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_code(
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


@router.get(
    "/submissions/{submission_id}",
    response_model=SubmissionStatusResponse,
)
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


# ── Public Helper Functions for Cross-Module Tools (e.g. Tutor Agent) ──


async def get_exercise_for_tutor(
    session: AsyncSession,
    exercise_id: UUID,
) -> ExerciseResponse | None:
    """Retrieve exercise details with hidden tests_code strictly stripped."""
    repo = ExerciseRepository(session)
    ex = await repo.get_by_id(exercise_id)
    if not ex:
        return None
    return ExerciseResponse.model_validate(ex)


async def get_submission_for_tutor(
    session: AsyncSession,
    submission_id: UUID,
) -> SubmissionStatusResponse | None:
    """Retrieve learner submission status and execution metrics."""
    repo = SubmissionRepository(session)
    sub = await repo.get_by_id(submission_id)
    if not sub:
        return None
    return SubmissionStatusResponse.model_validate(sub)


async def get_latest_submission_for_tutor(
    session: AsyncSession,
    user_id: UUID,
    exercise_id: UUID | None = None,
) -> SubmissionStatusResponse | None:
    """Retrieve latest submission for a user on a given exercise."""
    query = (
        select(Submission)
        .where(Submission.user_id == user_id)
        .order_by(Submission.created_at.desc())
    )
    if exercise_id is not None:
        query = query.where(Submission.exercise_id == exercise_id)
    result = await session.execute(query.limit(1))
    sub = result.scalar_one_or_none()
    if not sub:
        return None
    return SubmissionStatusResponse.model_validate(sub)


async def get_progress_for_tutor(
    session: AsyncSession,
    user_id: UUID,
    lesson_id: UUID | None = None,
    exercise_id: UUID | None = None,
) -> dict[str, Any]:
    """Retrieve learner attempt count and completion status."""
    repo = ProgressRepository(session)
    prog = await repo.get_by_target(user_id=user_id, lesson_id=lesson_id, exercise_id=exercise_id)
    if not prog:
        return {"completed": False, "attempts": 0}
    return {
        "completed": prog.completed,
        "attempts": prog.attempts,
        "updated_at": prog.updated_at.isoformat(),
    }


async def check_code_safely(
    session: AsyncSession,
    exercise_id: UUID,
    student_code: str,
) -> dict[str, Any]:
    """Evaluate code safely against exercise tests without leaking tests_code."""
    repo = ExerciseRepository(session)
    ex = await repo.get_by_id(exercise_id)
    if not ex or not ex.tests_code:
        return {"error": "Exercise not found or has no tests"}

    runner = SubprocessPythonRunner()
    result = await runner.run_submission(
        code=student_code,
        tests_code=ex.tests_code,
        timeout_seconds=3.0,
    )
    return {
        "status": result.status,
        "tests_passed": result.tests_passed,
        "tests_total": result.tests_total,
        "stderr": result.stderr[:300] if result.stderr else "",
        "stdout": result.stdout[:200] if result.stdout else "",
    }


__all__ = [
    "router",
    "EnrollmentResponse",
    "MyEnrollmentSummary",
    "ExerciseResponse",
    "ExerciseDetailResponse",
    "SubmissionQueuedResponse",
    "SubmissionStatusResponse",
    "ProgressResponse",
    "get_exercise_for_tutor",
    "get_submission_for_tutor",
    "get_latest_submission_for_tutor",
    "get_progress_for_tutor",
    "check_code_safely",
    "Exercise",
    "Submission",
]
