import re
import uuid
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.internal.models import Course, CourseModule, CourseStatus, Lesson
from app.modules.catalog.internal.repository import (
    CourseRepository,
    LessonRepository,
    ModuleRepository,
)
from app.modules.catalog.internal.schemas import (
    CourseCreateRequest,
    CourseDetailResponse,
    CourseSummaryResponse,
    CourseUpdateRequest,
    LessonCreateRequest,
    LessonDetailResponse,
    LessonReorderRequest,
    LessonSummaryResponse,
    LessonUpdateRequest,
    ModuleCreateRequest,
    ModuleDetailResponse,
    ModuleReorderRequest,
    ModuleResponse,
    ModuleUpdateRequest,
)


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    return re.sub(r"[\s-]+", "-", cleaned) or "course"


class CatalogService:
    @staticmethod
    def _to_summary_response(course: Course) -> CourseSummaryResponse:
        lesson_count = sum(len(m.lessons) for m in course.modules) if course.modules else 0
        module_count = len(course.modules) if course.modules else 0
        return CourseSummaryResponse(
            id=course.id,
            tenant_id=course.tenant_id,
            title=course.title,
            slug=course.slug,
            description=course.description,
            status=course.status,
            created_by=course.created_by,
            created_at=course.created_at,
            updated_at=course.updated_at,
            module_count=module_count,
            lesson_count=lesson_count,
        )

    @staticmethod
    def _to_detail_response(course: Course) -> CourseDetailResponse:
        modules_dto: list[ModuleDetailResponse] = []
        if course.modules:
            for mod in course.modules:
                lessons_dto = [LessonSummaryResponse.model_validate(les) for les in mod.lessons]
                modules_dto.append(
                    ModuleDetailResponse(
                        id=mod.id,
                        tenant_id=mod.tenant_id,
                        course_id=mod.course_id,
                        title=mod.title,
                        position=mod.position,
                        created_at=mod.created_at,
                        lessons=lessons_dto,
                    )
                )

        return CourseDetailResponse(
            id=course.id,
            tenant_id=course.tenant_id,
            title=course.title,
            slug=course.slug,
            description=course.description,
            status=course.status,
            created_by=course.created_by,
            created_at=course.created_at,
            updated_at=course.updated_at,
            modules=modules_dto,
        )

    async def list_courses(
        self,
        session: AsyncSession,
        user_role: str,
        published: bool | None = None,
        search: str | None = None,
    ) -> list[CourseSummaryResponse]:
        repo = CourseRepository(session)
        # Learner is strictly restricted to published courses at database query level
        published_only = (
            True if user_role == "student" else (published if published is not None else False)
        )
        courses = await repo.list_courses(published_only=published_only, search=search)
        return [self._to_summary_response(c) for c in courses]

    async def get_course(
        self,
        session: AsyncSession,
        course_id: UUID,
        user_role: str,
    ) -> CourseDetailResponse:
        repo = CourseRepository(session)
        course = await repo.get_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found",
            )

        if user_role == "student" and course.status != CourseStatus.PUBLISHED.value:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found",
            )

        return self._to_detail_response(course)

    async def create_course(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        req: CourseCreateRequest,
    ) -> CourseDetailResponse:
        repo = CourseRepository(session)
        base_slug = _slugify(req.slug or req.title)
        slug = base_slug

        # Ensure slug uniqueness in this tenant
        existing = await repo.get_by_slug(slug)
        counter = 1
        while existing:
            slug = f"{base_slug}-{counter}"
            existing = await repo.get_by_slug(slug)
            counter += 1

        initial_status = (
            CourseStatus.PUBLISHED.value
            if req.status == CourseStatus.PUBLISHED.value
            else CourseStatus.DRAFT.value
        )

        course = Course(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            title=req.title,
            slug=slug,
            description=req.description,
            status=initial_status,
            created_by=user_id,
        )
        created = await repo.create(course)
        # Fetch with relationships initialized
        loaded = await repo.get_by_id(created.id)
        return self._to_detail_response(loaded or created)

    async def update_course(
        self,
        session: AsyncSession,
        course_id: UUID,
        req: CourseUpdateRequest,
    ) -> CourseDetailResponse:
        repo = CourseRepository(session)
        course = await repo.get_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found",
            )

        if req.title is not None:
            course.title = req.title
        if req.description is not None:
            course.description = req.description
        if req.status is not None:
            course.status = req.status
        if req.slug is not None:
            new_slug = _slugify(req.slug)
            if new_slug != course.slug:
                existing = await repo.get_by_slug(new_slug)
                if existing and existing.id != course.id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="A course with this slug already exists",
                    )
                course.slug = new_slug

        updated = await repo.update(course)
        return self._to_detail_response(updated)

    async def publish_course(
        self,
        session: AsyncSession,
        course_id: UUID,
        new_status: str,
    ) -> CourseDetailResponse:
        repo = CourseRepository(session)
        course = await repo.get_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found",
            )
        course.status = new_status
        updated = await repo.update(course)
        return self._to_detail_response(updated)

    async def delete_course(
        self,
        session: AsyncSession,
        course_id: UUID,
    ) -> None:
        repo = CourseRepository(session)
        course = await repo.get_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found",
            )
        await repo.delete(course)

    # ── Module Management ──

    async def create_module(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        req: ModuleCreateRequest,
    ) -> ModuleDetailResponse:
        course_repo = CourseRepository(session)
        course = await course_repo.get_by_id(req.course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found",
            )

        mod_repo = ModuleRepository(session)
        pos = (
            req.position
            if req.position is not None
            else await mod_repo.get_next_position(req.course_id)
        )

        module = CourseModule(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            course_id=req.course_id,
            title=req.title,
            position=pos,
        )
        created = await mod_repo.create(module)
        return ModuleDetailResponse(
            id=created.id,
            tenant_id=created.tenant_id,
            course_id=created.course_id,
            title=created.title,
            position=created.position,
            created_at=created.created_at,
            lessons=[],
        )

    async def update_module(
        self,
        session: AsyncSession,
        module_id: UUID,
        req: ModuleUpdateRequest,
    ) -> ModuleResponse:
        mod_repo = ModuleRepository(session)
        module = await mod_repo.get_by_id(module_id)
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found",
            )
        if req.title is not None:
            module.title = req.title
        if req.position is not None:
            module.position = req.position

        updated = await mod_repo.update(module)
        return ModuleResponse.model_validate(updated)

    async def delete_module(
        self,
        session: AsyncSession,
        module_id: UUID,
    ) -> None:
        mod_repo = ModuleRepository(session)
        module = await mod_repo.get_by_id(module_id)
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found",
            )
        await mod_repo.delete(module)

    async def reorder_modules(
        self,
        session: AsyncSession,
        req: ModuleReorderRequest,
    ) -> list[ModuleResponse]:
        mod_repo = ModuleRepository(session)
        reordered = await mod_repo.reorder(req.course_id, req.ordered_module_ids)
        return [ModuleResponse.model_validate(m) for m in reordered]

    # ── Lesson Management ──

    async def create_lesson(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        req: LessonCreateRequest,
    ) -> LessonDetailResponse:
        mod_repo = ModuleRepository(session)
        module = await mod_repo.get_by_id(req.module_id)
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found",
            )

        lesson_repo = LessonRepository(session)
        pos = (
            req.position
            if req.position is not None
            else await lesson_repo.get_next_position(req.module_id)
        )

        lesson = Lesson(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            module_id=req.module_id,
            title=req.title,
            content_md=req.content_md,
            position=pos,
        )
        created = await lesson_repo.create(lesson)
        return LessonDetailResponse.model_validate(created)

    async def update_lesson(
        self,
        session: AsyncSession,
        lesson_id: UUID,
        req: LessonUpdateRequest,
    ) -> LessonDetailResponse:
        lesson_repo = LessonRepository(session)
        lesson = await lesson_repo.get_by_id(lesson_id)
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found",
            )
        if req.title is not None:
            lesson.title = req.title
        if req.content_md is not None:
            lesson.content_md = req.content_md
        if req.position is not None:
            lesson.position = req.position

        updated = await lesson_repo.update(lesson)
        return LessonDetailResponse.model_validate(updated)

    async def delete_lesson(
        self,
        session: AsyncSession,
        lesson_id: UUID,
    ) -> None:
        lesson_repo = LessonRepository(session)
        lesson = await lesson_repo.get_by_id(lesson_id)
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found",
            )
        await lesson_repo.delete(lesson)

    async def reorder_lessons(
        self,
        session: AsyncSession,
        req: LessonReorderRequest,
    ) -> list[LessonSummaryResponse]:
        lesson_repo = LessonRepository(session)
        reordered = await lesson_repo.reorder(req.module_id, req.ordered_lesson_ids)
        return [LessonSummaryResponse.model_validate(les) for les in reordered]

    async def get_lesson(
        self,
        session: AsyncSession,
        lesson_id: UUID,
        user_role: str,
    ) -> LessonDetailResponse:
        lesson_repo = LessonRepository(session)
        published_only = user_role == "student"
        lesson = await lesson_repo.get_by_id(lesson_id, published_only=published_only)
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found",
            )
        return LessonDetailResponse.model_validate(lesson)
