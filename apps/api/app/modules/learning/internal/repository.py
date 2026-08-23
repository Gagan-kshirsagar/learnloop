from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.catalog.api import CourseModule, Lesson
from app.modules.learning.internal.models import (
    Enrollment,
    Exercise,
    Progress,
    Submission,
)


class EnrollmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user_and_course(self, user_id: UUID, course_id: UUID) -> Enrollment | None:
        query = select(Enrollment).where(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID) -> list[Enrollment]:
        query = (
            select(Enrollment)
            .where(Enrollment.user_id == user_id)
            .order_by(Enrollment.enrolled_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, enrollment: Enrollment) -> Enrollment:
        self.session.add(enrollment)
        await self.session.flush()
        return enrollment


class ExerciseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, exercise_id: UUID) -> Exercise | None:
        query = select(Exercise).where(Exercise.id == exercise_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_lesson_id(self, lesson_id: UUID) -> Exercise | None:
        query = select(Exercise).where(Exercise.lesson_id == lesson_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, exercise: Exercise) -> Exercise:
        self.session.add(exercise)
        await self.session.flush()
        return exercise

    async def update(self, exercise: Exercise) -> Exercise:
        await self.session.flush()
        return exercise


class SubmissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, submission: Submission) -> Submission:
        self.session.add(submission)
        await self.session.flush()
        return submission

    async def get_by_id(self, submission_id: UUID) -> Submission | None:
        query = (
            select(Submission)
            .options(selectinload(Submission.exercise))
            .where(Submission.id == submission_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, submission: Submission) -> Submission:
        await self.session.flush()
        return submission

    async def get_last_submission_time(self, user_id: UUID) -> datetime | None:
        query = select(func.max(Submission.created_at)).where(Submission.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class ProgressRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_target(
        self,
        user_id: UUID,
        lesson_id: UUID | None = None,
        exercise_id: UUID | None = None,
    ) -> Progress | None:
        query = select(Progress).where(Progress.user_id == user_id)
        if lesson_id is not None:
            query = query.where(Progress.lesson_id == lesson_id)
        if exercise_id is not None:
            query = query.where(Progress.exercise_id == exercise_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def record_lesson_completion(
        self,
        tenant_id: UUID,
        user_id: UUID,
        lesson_id: UUID,
        completed: bool = True,
    ) -> Progress:
        progress = await self.get_by_target(user_id=user_id, lesson_id=lesson_id)
        if progress:
            progress.completed = completed
            progress.attempts += 1
            progress.updated_at = datetime.now(UTC)
        else:
            progress = Progress(
                tenant_id=tenant_id,
                user_id=user_id,
                lesson_id=lesson_id,
                exercise_id=None,
                completed=completed,
                attempts=1,
            )
            self.session.add(progress)
        await self.session.flush()
        return progress

    async def record_exercise_attempt(
        self,
        tenant_id: UUID,
        user_id: UUID,
        exercise_id: UUID,
        passed: bool,
    ) -> Progress:
        progress = await self.get_by_target(user_id=user_id, exercise_id=exercise_id)
        if progress:
            if passed:
                progress.completed = True
            progress.attempts += 1
            progress.updated_at = datetime.now(UTC)
        else:
            progress = Progress(
                tenant_id=tenant_id,
                user_id=user_id,
                lesson_id=None,
                exercise_id=exercise_id,
                completed=passed,
                attempts=1,
            )
            self.session.add(progress)
        await self.session.flush()
        return progress

    async def count_completed_lessons_in_course(self, user_id: UUID, course_id: UUID) -> int:
        query = (
            select(func.count(Progress.id))
            .join(Lesson, Progress.lesson_id == Lesson.id)
            .join(CourseModule, Lesson.module_id == CourseModule.id)
            .where(
                CourseModule.course_id == course_id,
                Progress.user_id == user_id,
                Progress.completed.is_(True),
            )
        )
        result = await self.session.execute(query)
        return int(result.scalar_one() or 0)
