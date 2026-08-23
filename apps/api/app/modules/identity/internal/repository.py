from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.internal.models import Tenant, User, UserRole, UserStatus


class TenantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, name: str, slug: str, plan: str = "free") -> Tenant:
        tenant = Tenant(name=name, slug=slug, plan=plan)
        self.session.add(tenant)
        await self.session.flush()
        await self.session.refresh(tenant)
        return tenant

    async def get_by_id(self, tenant_id: UUID) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        tenant_id: UUID,
        email: str,
        name: str,
        role: str = UserRole.STUDENT,
        password_hash: str | None = None,
        status: str = UserStatus.ACTIVE,
    ) -> User:
        user = User(
            tenant_id=tenant_id,
            email=email.lower().strip(),
            name=name.strip(),
            role=role,
            password_hash=password_hash,
            status=status,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email_and_tenant(self, email: str, tenant_id: UUID) -> User | None:
        stmt = select(User).where(
            User.email == email.lower().strip(),
            User.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email_unscoped(self, email: str) -> list[User]:
        stmt = select(User).where(User.email == email.lower().strip())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
