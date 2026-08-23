from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.internal.auth_provider import AuthProvider, get_auth_provider
from app.modules.identity.internal.dependencies import (
    get_current_token_payload,
    get_current_user,
    get_tenant_db_session,
    require_role,
)
from app.modules.identity.internal.schemas import (
    AuthResponse,
    LoginRequest,
    MeResponse,
    RefreshRequest,
    RegisterRequest,
    TenantResponse,
    TokenPayload,
    TokenResponse,
    UserResponse,
)
from app.modules.identity.internal.service import IdentityService
from app.shared.db import get_privileged_session

router = APIRouter(prefix="/auth", tags=["auth"])


def get_identity_service(
    auth_provider: AuthProvider = Depends(get_auth_provider),
) -> IdentityService:
    return IdentityService(auth_provider=auth_provider)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest,
    service: IdentityService = Depends(get_identity_service),
    session: AsyncSession = Depends(get_privileged_session),
) -> AuthResponse:
    async with session.begin():
        return await service.register(session, req)


@router.post("/login", response_model=AuthResponse)
async def login(
    req: LoginRequest,
    service: IdentityService = Depends(get_identity_service),
    session: AsyncSession = Depends(get_privileged_session),
) -> AuthResponse:
    async with session.begin():
        return await service.login(session, req)


@router.post("/guest", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def guest_login(
    service: IdentityService = Depends(get_identity_service),
    session: AsyncSession = Depends(get_privileged_session),
) -> AuthResponse:
    async with session.begin():
        return await service.create_guest(session)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    req: RefreshRequest,
    service: IdentityService = Depends(get_identity_service),
    session: AsyncSession = Depends(get_privileged_session),
) -> TokenResponse:
    if not req.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required",
        )
    async with session.begin():
        return await service.refresh_tokens(session, req.refresh_token)


@router.get("/me", response_model=MeResponse)
async def get_me(
    payload: TokenPayload = Depends(get_current_token_payload),
    service: IdentityService = Depends(get_identity_service),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> MeResponse:
    user_id = UUID(payload.sub)
    tenant_id = UUID(payload.tenant_id)
    return await service.get_me(session, user_id=user_id, tenant_id=tenant_id)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout() -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = [
    "router",
    "get_current_user",
    "get_current_token_payload",
    "get_tenant_db_session",
    "require_role",
    "UserResponse",
    "TenantResponse",
    "TokenPayload",
    "AuthResponse",
    "TokenResponse",
    "MeResponse",
]
