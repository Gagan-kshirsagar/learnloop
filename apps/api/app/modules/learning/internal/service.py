import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.catalog.api import Course, CourseModule, Lesson
from app.modules.learning.internal.models import (
    Enrollment,
    EnrollmentStatus,
    Exercise,
    Submission,
    SubmissionStatus,
)
from app.modules.learning.internal.repository import (
    EnrollmentRepository,
    ExerciseRepository,
    ProgressRepository,
    SubmissionRepository,
)
from app.modules.learning.internal.runner import CodeRunnerProtocol, SubprocessPythonRunner
from app.modules.learning.internal.schemas import (
    EnrollmentResponse,
    ExerciseCreateUpdateRequest,
    ExerciseDetailResponse,
    ExerciseResponse,
    MyEnrollmentSummary,
    ProgressResponse,
    SubmissionQueuedResponse,
    SubmissionStatusResponse,
    SubmitCodeRequest,
)
from app.shared.db import get_session_factory, set_tenant_context


class LearningService:
    def __init__(
        self,
        runner: CodeRunnerProtocol | None = None,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self.runner = runner or SubprocessPythonRunner()
        self.session_factory = session_factory or get_session_factory()

    async def enroll(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        course_id: UUID,
    ) -> EnrollmentResponse:
        course_query = select(Course).where(Course.id == course_id)
        result = await session.execute(course_query)
        course = result.scalar_one_or_none()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found",
            )

        repo = EnrollmentRepository(session)
        existing = await repo.get_by_user_and_course(user_id=user_id, course_id=course_id)
        if existing:
            return EnrollmentResponse.model_validate(existing)

        enrollment = Enrollment(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            course_id=course_id,
            status=EnrollmentStatus.ACTIVE.value,
        )
        created = await repo.create(enrollment)
        return EnrollmentResponse.model_validate(created)

    async def list_my_enrollments(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> list[MyEnrollmentSummary]:
        enrollment_repo = EnrollmentRepository(session)
        progress_repo = ProgressRepository(session)
        enrollments = await enrollment_repo.list_by_user(user_id)

        summaries: list[MyEnrollmentSummary] = []
        for enr in enrollments:
            # Query course info and lesson count
            c_query = select(Course).where(Course.id == enr.course_id)
            c_res = await session.execute(c_query)
            course = c_res.scalar_one_or_none()
            if not course:
                continue

            lessons_count_query = (
                select(func.count(Lesson.id))
                .join(CourseModule, Lesson.module_id == CourseModule.id)
                .where(CourseModule.course_id == course.id)
            )
            total_lessons_res = await session.execute(lessons_count_query)
            total_lessons = int(total_lessons_res.scalar_one() or 0)

            completed_lessons = await progress_repo.count_completed_lessons_in_course(
                user_id=user_id, course_id=course.id
            )

            pct = int(completed_lessons / total_lessons * 100) if total_lessons > 0 else 0

            summaries.append(
                MyEnrollmentSummary(
                    id=enr.id,
                    course_id=course.id,
                    course_title=course.title,
                    course_slug=course.slug,
                    course_description=course.description,
                    status=enr.status,
                    enrolled_at=enr.enrolled_at,
                    total_lessons=total_lessons,
                    completed_lessons=completed_lessons,
                    progress_percentage=pct,
                )
            )

        return summaries

    async def get_exercise_for_learner(
        self,
        session: AsyncSession,
        lesson_id: UUID,
    ) -> ExerciseResponse | None:
        repo = ExerciseRepository(session)
        exercise = await repo.get_by_lesson_id(lesson_id)
        if not exercise:
            return None
        # tests_code is omitted from ExerciseResponse
        return ExerciseResponse.model_validate(exercise)

    async def get_exercise_for_author(
        self,
        session: AsyncSession,
        lesson_id: UUID,
    ) -> ExerciseDetailResponse:
        repo = ExerciseRepository(session)
        exercise = await repo.get_by_lesson_id(lesson_id)
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No exercise found for this lesson",
            )
        return ExerciseDetailResponse.model_validate(exercise)

    async def save_exercise_author(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        lesson_id: UUID,
        req: ExerciseCreateUpdateRequest,
    ) -> ExerciseDetailResponse:
        # Verify lesson exists
        les_query = select(Lesson).where(Lesson.id == lesson_id)
        res = await session.execute(les_query)
        lesson = res.scalar_one_or_none()
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found",
            )

        repo = ExerciseRepository(session)
        exercise = await repo.get_by_lesson_id(lesson_id)
        if exercise:
            exercise.prompt_md = req.prompt_md
            exercise.starter_code = req.starter_code
            exercise.tests_code = req.tests_code
            exercise.language = req.language
            updated = await repo.update(exercise)
            return ExerciseDetailResponse.model_validate(updated)

        new_exercise = Exercise(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            lesson_id=lesson_id,
            prompt_md=req.prompt_md,
            starter_code=req.starter_code,
            tests_code=req.tests_code,
            language=req.language,
        )
        created = await repo.create(new_exercise)
        return ExerciseDetailResponse.model_validate(created)

    async def submit_code(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        user_role: str,
        exercise_id: UUID,
        req: SubmitCodeRequest,
    ) -> SubmissionQueuedResponse:
        ex_repo = ExerciseRepository(session)
        exercise = await ex_repo.get_by_id(exercise_id)
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found",
            )

        # Verify enrollment for student
        if user_role == "student":
            les_query = (
                select(CourseModule.course_id)
                .join(Lesson, Lesson.module_id == CourseModule.id)
                .where(Lesson.id == exercise.lesson_id)
            )
            c_res = await session.execute(les_query)
            course_id = c_res.scalar_one_or_none()
            if not course_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Course for exercise not found",
                )

            enr_repo = EnrollmentRepository(session)
            enrollment = await enr_repo.get_by_user_and_course(user_id=user_id, course_id=course_id)
            if not enrollment:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You must enroll in the course before submitting exercises.",
                )

        sub_repo = SubmissionRepository(session)

        # Rate Limit Guard: 1 submission per 2 seconds per user
        last_time = await sub_repo.get_last_submission_time(user_id)
        if last_time and (datetime.now(UTC) - last_time) < timedelta(seconds=2):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait a few seconds before submitting again.",
            )

        submission = Submission(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            exercise_id=exercise_id,
            code=req.code,
            status=SubmissionStatus.QUEUED.value,
        )
        created = await sub_repo.create(submission)

        # Dispatch async background worker task
        asyncio.create_task(
            self.process_submission_background(
                submission_id=created.id,
                tenant_id=tenant_id,
                code=req.code,
                tests_code=exercise.tests_code,
            )
        )

        return SubmissionQueuedResponse(submission_id=created.id, status="queued")

    async def process_submission_background(
        self,
        submission_id: UUID,
        tenant_id: UUID,
        code: str,
        tests_code: str,
    ) -> None:
        factory = self.session_factory
        async with factory() as session, session.begin():
            await set_tenant_context(session, tenant_id)
            sub_repo = SubmissionRepository(session)
            submission = await sub_repo.get_by_id(submission_id)
            if not submission:
                return

            submission.status = SubmissionStatus.RUNNING.value
            await sub_repo.update(submission)

        # Run code outside DB transaction lock
        runner_result = await self.runner.run_submission(code=code, tests_code=tests_code)

        # Save final evaluation results
        async with factory() as session, session.begin():
            await set_tenant_context(session, tenant_id)
            sub_repo = SubmissionRepository(session)
            prog_repo = ProgressRepository(session)

            submission = await sub_repo.get_by_id(submission_id)
            if not submission:
                return

            submission.status = runner_result.status
            submission.stdout = runner_result.stdout
            submission.stderr = runner_result.stderr
            submission.tests_passed = runner_result.tests_passed
            submission.tests_total = runner_result.tests_total
            submission.duration_ms = runner_result.duration_ms
            await sub_repo.update(submission)

            # Record progress
            passed = runner_result.status == "passed"
            await prog_repo.record_exercise_attempt(
                tenant_id=tenant_id,
                user_id=submission.user_id,
                exercise_id=submission.exercise_id,
                passed=passed,
            )

    async def get_submission_status(
        self,
        session: AsyncSession,
        submission_id: UUID,
        user_id: UUID,
        user_role: str,
    ) -> SubmissionStatusResponse:
        sub_repo = SubmissionRepository(session)
        submission = await sub_repo.get_by_id(submission_id)
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found",
            )

        if user_role == "student" and submission.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found",
            )

        return SubmissionStatusResponse.model_validate(submission)

    async def complete_lesson(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        lesson_id: UUID,
        completed: bool = True,
    ) -> ProgressResponse:
        les_query = select(Lesson).where(Lesson.id == lesson_id)
        res = await session.execute(les_query)
        lesson = res.scalar_one_or_none()
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found",
            )

        prog_repo = ProgressRepository(session)
        progress = await prog_repo.record_lesson_completion(
            tenant_id=tenant_id,
            user_id=user_id,
            lesson_id=lesson_id,
            completed=completed,
        )
        return ProgressResponse.model_validate(progress)
