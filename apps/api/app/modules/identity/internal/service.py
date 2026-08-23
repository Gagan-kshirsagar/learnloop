import re
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.internal.auth_provider import AuthProvider, get_auth_provider
from app.modules.identity.internal.models import UserRole, UserStatus
from app.modules.identity.internal.repository import TenantRepository, UserRepository
from app.modules.identity.internal.schemas import (
    AuthResponse,
    LoginRequest,
    MeResponse,
    RegisterRequest,
    TenantResponse,
    TokenResponse,
    UserResponse,
)


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return cleaned or f"org-{uuid4().hex[:6]}"


class IdentityService:
    def __init__(self, auth_provider: AuthProvider | None = None) -> None:
        self.auth_provider = auth_provider or get_auth_provider()

    async def register(self, session: AsyncSession, req: RegisterRequest) -> AuthResponse:
        tenant_repo = TenantRepository(session)
        user_repo = UserRepository(session)

        base_slug = slugify(req.org_name)
        slug = base_slug
        if await tenant_repo.get_by_slug(slug):
            slug = f"{base_slug}-{uuid4().hex[:6]}"

        tenant = await tenant_repo.create(name=req.org_name, slug=slug, plan="free")

        # Check if email is already used in this tenant (safeguard)
        existing = await user_repo.get_by_email_and_tenant(req.email, tenant.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists in the organization",
            )

        password_hash = self.auth_provider.hash_password(req.password)
        user = await user_repo.create(
            tenant_id=tenant.id,
            email=req.email,
            name=req.name,
            role=UserRole.OWNER,
            password_hash=password_hash,
            status=UserStatus.ACTIVE,
        )

        access_token = self.auth_provider.create_access_token(
            user_id=user.id,
            tenant_id=tenant.id,
            role=user.role,
        )
        refresh_token = self.auth_provider.create_refresh_token(
            user_id=user.id,
            tenant_id=tenant.id,
            role=user.role,
        )

        return AuthResponse(
            user=UserResponse.model_validate(user),
            tenant=TenantResponse.model_validate(tenant),
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
            ),
        )

    async def login(self, session: AsyncSession, req: LoginRequest) -> AuthResponse:
        user_repo = UserRepository(session)
        tenant_repo = TenantRepository(session)

        # Pre-login lookup across tenants
        candidates = await user_repo.get_by_email_unscoped(req.email)
        matched_user = None

        for candidate in candidates:
            if (
                candidate.password_hash
                and self.auth_provider.verify_password(req.password, candidate.password_hash)
                and candidate.status == UserStatus.ACTIVE
            ):
                matched_user = candidate
                break

        if not matched_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        tenant = await tenant_repo.get_by_id(matched_user.tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        access_token = self.auth_provider.create_access_token(
            user_id=matched_user.id,
            tenant_id=tenant.id,
            role=matched_user.role,
        )
        refresh_token = self.auth_provider.create_refresh_token(
            user_id=matched_user.id,
            tenant_id=tenant.id,
            role=matched_user.role,
        )

        return AuthResponse(
            user=UserResponse.model_validate(matched_user),
            tenant=TenantResponse.model_validate(tenant),
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
            ),
        )

    async def create_guest(self, session: AsyncSession) -> AuthResponse:
        tenant_repo = TenantRepository(session)
        user_repo = UserRepository(session)

        sandbox_id = uuid4().hex[:8]
        slug = f"demo-guest-{sandbox_id}"
        tenant = await tenant_repo.create(
            name="Demo Sandbox",
            slug=slug,
            plan="free",
        )

        guest_email = f"guest-{sandbox_id}@demo.learnloop.dev"
        user = await user_repo.create(
            tenant_id=tenant.id,
            email=guest_email,
            name="Guest Learner",
            role=UserRole.STUDENT,
            password_hash=None,
            status=UserStatus.ACTIVE,
        )

        access_token = self.auth_provider.create_access_token(
            user_id=user.id,
            tenant_id=tenant.id,
            role=user.role,
        )
        refresh_token = self.auth_provider.create_refresh_token(
            user_id=user.id,
            tenant_id=tenant.id,
            role=user.role,
        )

        return AuthResponse(
            user=UserResponse.model_validate(user),
            tenant=TenantResponse.model_validate(tenant),
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
            ),
        )

    async def refresh_tokens(self, session: AsyncSession, refresh_token: str) -> TokenResponse:
        try:
            payload = self.auth_provider.verify_token(refresh_token, expected_type="refresh")
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            ) from exc

        user_id = UUID(payload.sub)
        tenant_id = UUID(payload.tenant_id)

        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id)
        if not user or user.tenant_id != tenant_id or user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User inactive or does not exist",
            )

        new_access_token = self.auth_provider.create_access_token(
            user_id=user.id,
            tenant_id=tenant_id,
            role=user.role,
        )
        new_refresh_token = self.auth_provider.create_refresh_token(
            user_id=user.id,
            tenant_id=tenant_id,
            role=user.role,
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )

    async def get_me(self, session: AsyncSession, user_id: UUID, tenant_id: UUID) -> MeResponse:
        user_repo = UserRepository(session)
        tenant_repo = TenantRepository(session)

        user = await user_repo.get_by_id(user_id)
        tenant = await tenant_repo.get_by_id(tenant_id)

        if not user or not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User or organization not found",
            )

        return MeResponse(
            user=UserResponse.model_validate(user),
            tenant=TenantResponse.model_validate(tenant),
        )
