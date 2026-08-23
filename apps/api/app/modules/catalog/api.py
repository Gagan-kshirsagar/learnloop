from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.internal.schemas import (
    CourseCreateRequest,
    CourseDetailResponse,
    CourseStatusRequest,
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
from app.modules.catalog.internal.service import CatalogService
from app.modules.identity.api import (
    UserResponse,
    get_current_user,
    get_tenant_db_session,
    require_role,
)

router = APIRouter(prefix="/catalog", tags=["catalog"])


def get_catalog_service() -> CatalogService:
    return CatalogService()


# ── Learner / Read Endpoints ──


@router.get("/courses", response_model=list[CourseSummaryResponse])
async def list_courses(
    published: bool | None = None,
    search: str | None = None,
    current_user: UserResponse = Depends(get_current_user),
    service: CatalogService = Depends(get_catalog_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> list[CourseSummaryResponse]:
    return await service.list_courses(
        session,
        user_role=current_user.role,
        published=published,
        search=search,
    )


@router.get("/courses/{course_id}", response_model=CourseDetailResponse)
async def get_course(
    course_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    service: CatalogService = Depends(get_catalog_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> CourseDetailResponse:
    return await service.get_course(
        session,
        course_id=course_id,
        user_role=current_user.role,
    )


@router.get("/lessons/{lesson_id}", response_model=LessonDetailResponse)
async def get_lesson(
    lesson_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    service: CatalogService = Depends(get_catalog_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> LessonDetailResponse:
    return await service.get_lesson(
        session,
        lesson_id=lesson_id,
        user_role=current_user.role,
    )


# ── Author Course Endpoints (Instructor / Owner only) ──


@router.post(
    "/courses",
    response_model=CourseDetailResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("owner", "instructor"))],
)
async def create_course(
    req: CourseCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    service: CatalogService = Depends(get_catalog_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> CourseDetailResponse:
    return await service.create_course(
        session,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        req=req,
    )


@router.patch(
    "/courses/{course_id}",
    response_model=CourseDetailResponse,
    dependencies=[Depends(require_role("owner", "instructor"))],
)
async def update_course(
    course_id: UUID,
    req: CourseUpdateRequest,
    service: CatalogService = Depends(get_catalog_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> CourseDetailResponse:
    return await service.update_course(session, course_id=course_id, req=req)


@router.post(
    "/courses/{course_id}/publish",
    response_model=CourseDetailResponse,
    dependencies=[Depends(require_role("owner", "instructor"))],
)
async def publish_course(
    course_id: UUID,
    req: CourseStatusRequest,
    service: CatalogService = Depends(get_catalog_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> CourseDetailResponse:
    return await service.publish_course(session, course_id=course_id, new_status=req.status)


@router.delete(
    "/courses/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("owner", "instructor"))],
)
async def delete_course(
    course_id: UUID,
    service: CatalogService = Depends(get_catalog_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> Response:
    await service.delete_course(session, course_id=course_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Author Module Endpoints ──


@router.post(
    "/modules",
    response_model=ModuleDetailResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("owner", "instructor"))],
)
async def create_module(
    req: ModuleCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    service: CatalogService = Depends(get_catalog_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> ModuleDetailResponse:
    return await service.create_module(
        session,
        tenant_id=current_user.tenant_id,
        req=req,
    )


@router.patch(
    "/modules/{module_id}",
    response_model=ModuleResponse,
    dependencies=[Depends(require_role("owner", "instructor"))],
)
async def update_module(
    module_id: UUID,
    req: ModuleUpdateRequest,
    service: CatalogService = Depends(get_catalog_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> ModuleResponse:
    return await service.update_module(session, module_id=module_id, req=req)


@router.delete(
    "/modules/{module_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("owner", "instructor"))],
)
async def delete_module(
    module_id: UUID,
    service: CatalogService = Depends(get_catalog_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> Response:
    await service.delete_module(session, module_id=module_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/modules/reorder",
    response_model=list[ModuleResponse],
    dependencies=[Depends(require_role("owner", "instructor"))],
)
async def reorder_modules(
    req: ModuleReorderRequest,
    service: CatalogService = Depends(get_catalog_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> list[ModuleResponse]:
    return await service.reorder_modules(session, req=req)


# ── Author Lesson Endpoints ──


@router.post(
    "/lessons",
    response_model=LessonDetailResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("owner", "instructor"))],
)
async def create_lesson(
    req: LessonCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    service: CatalogService = Depends(get_catalog_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> LessonDetailResponse:
    return await service.create_lesson(
        session,
        tenant_id=current_user.tenant_id,
        req=req,
    )


@router.patch(
    "/lessons/{lesson_id}",
    response_model=LessonDetailResponse,
    dependencies=[Depends(require_role("owner", "instructor"))],
)
async def update_lesson(
    lesson_id: UUID,
    req: LessonUpdateRequest,
    service: CatalogService = Depends(get_catalog_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> LessonDetailResponse:
    return await service.update_lesson(session, lesson_id=lesson_id, req=req)


@router.delete(
    "/lessons/{lesson_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("owner", "instructor"))],
)
async def delete_lesson(
    lesson_id: UUID,
    service: CatalogService = Depends(get_catalog_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> Response:
    await service.delete_lesson(session, lesson_id=lesson_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/lessons/reorder",
    response_model=list[LessonSummaryResponse],
    dependencies=[Depends(require_role("owner", "instructor"))],
)
async def reorder_lessons(
    req: LessonReorderRequest,
    service: CatalogService = Depends(get_catalog_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> list[LessonSummaryResponse]:
    return await service.reorder_lessons(session, req=req)


__all__ = [
    "router",
    "CourseSummaryResponse",
    "CourseDetailResponse",
    "ModuleDetailResponse",
    "LessonDetailResponse",
    "LessonSummaryResponse",
]
