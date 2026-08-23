from collections.abc import AsyncIterator, Callable
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.identity.internal.auth_provider import AuthProvider, get_auth_provider
from app.modules.identity.internal.models import UserStatus
from app.modules.identity.internal.repository import UserRepository
from app.modules.identity.internal.schemas import TokenPayload, UserResponse
from app.shared.db import get_session_factory, set_tenant_context

security_scheme = HTTPBearer(auto_error=True)


def get_current_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    auth_provider: AuthProvider = Depends(get_auth_provider),
) -> TokenPayload:
    try:
        return auth_provider.verify_token(credentials.credentials, expected_type="access")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_tenant_db_session(
    payload: TokenPayload = Depends(get_current_token_payload),
    factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> AsyncIterator[AsyncSession]:
    tenant_id = UUID(payload.tenant_id)
    async with factory() as session, session.begin():
        await set_tenant_context(session, tenant_id)
        yield session


async def get_current_user(
    payload: TokenPayload = Depends(get_current_token_payload),
    session: AsyncSession = Depends(get_tenant_db_session),
) -> UserResponse:
    user_id = UUID(payload.sub)
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)

    if not user or user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserResponse.model_validate(user)


def require_role(*allowed_roles: str) -> Callable[..., Any]:
    async def role_checker(
        current_user: UserResponse = Depends(get_current_user),
    ) -> UserResponse:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this operation",
            )
        return current_user

    return role_checker
