from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.catalog.internal.models import Course, CourseModule, CourseStatus, Lesson


class CourseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_courses(
        self,
        published_only: bool = False,
        search: str | None = None,
    ) -> list[Course]:
        query = (
            select(Course)
            .options(selectinload(Course.modules).selectinload(CourseModule.lessons))
            .order_by(Course.created_at.desc())
        )

        if published_only:
            query = query.where(Course.status == CourseStatus.PUBLISHED.value)

        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Course.title.ilike(pattern),
                    Course.description.ilike(pattern),
                )
            )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, course_id: UUID) -> Course | None:
        query = (
            select(Course)
            .options(selectinload(Course.modules).selectinload(CourseModule.lessons))
            .where(Course.id == course_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Course | None:
        query = select(Course).where(Course.slug == slug)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, course: Course) -> Course:
        self.session.add(course)
        await self.session.flush()
        return course

    async def update(self, course: Course) -> Course:
        await self.session.flush()
        return course

    async def delete(self, course: Course) -> None:
        await self.session.delete(course)
        await self.session.flush()


class ModuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, module_id: UUID) -> CourseModule | None:
        query = (
            select(CourseModule)
            .options(selectinload(CourseModule.lessons))
            .where(CourseModule.id == module_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_course(self, course_id: UUID) -> list[CourseModule]:
        query = (
            select(CourseModule)
            .options(selectinload(CourseModule.lessons))
            .where(CourseModule.course_id == course_id)
            .order_by(CourseModule.position.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_next_position(self, course_id: UUID) -> int:
        query = select(func.coalesce(func.max(CourseModule.position), -1)).where(
            CourseModule.course_id == course_id
        )
        result = await self.session.execute(query)
        max_pos = result.scalar_one()
        return int(max_pos) + 1

    async def create(self, module: CourseModule) -> CourseModule:
        self.session.add(module)
        await self.session.flush()
        return module

    async def update(self, module: CourseModule) -> CourseModule:
        await self.session.flush()
        return module

    async def delete(self, module: CourseModule) -> None:
        await self.session.delete(module)
        await self.session.flush()

    async def reorder(self, course_id: UUID, ordered_ids: list[UUID]) -> list[CourseModule]:
        for position, mod_id in enumerate(ordered_ids):
            module = await self.get_by_id(mod_id)
            if module and module.course_id == course_id:
                module.position = position
        await self.session.flush()
        return await self.list_by_course(course_id)


class LessonRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, lesson_id: UUID, published_only: bool = False) -> Lesson | None:
        query = (
            select(Lesson)
            .options(selectinload(Lesson.module).selectinload(CourseModule.course))
            .where(Lesson.id == lesson_id)
        )
        if published_only:
            query = (
                query.join(CourseModule, Lesson.module_id == CourseModule.id)
                .join(Course, CourseModule.course_id == Course.id)
                .where(Course.status == CourseStatus.PUBLISHED.value)
            )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_module(self, module_id: UUID) -> list[Lesson]:
        query = select(Lesson).where(Lesson.module_id == module_id).order_by(Lesson.position.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_next_position(self, module_id: UUID) -> int:
        query = select(func.coalesce(func.max(Lesson.position), -1)).where(
            Lesson.module_id == module_id
        )
        result = await self.session.execute(query)
        max_pos = result.scalar_one()
        return int(max_pos) + 1

    async def create(self, lesson: Lesson) -> Lesson:
        self.session.add(lesson)
        await self.session.flush()
        return lesson

    async def update(self, lesson: Lesson) -> Lesson:
        await self.session.flush()
        return lesson

    async def delete(self, lesson: Lesson) -> None:
        await self.session.delete(lesson)
        await self.session.flush()

    async def reorder(self, module_id: UUID, ordered_ids: list[UUID]) -> list[Lesson]:
        for position, les_id in enumerate(ordered_ids):
            lesson = await self.get_by_id(les_id)
            if lesson and lesson.module_id == module_id:
                lesson.position = position
        await self.session.flush()
        return await self.list_by_module(module_id)
