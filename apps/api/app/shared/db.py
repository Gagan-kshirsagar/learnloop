from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import Depends
from sqlalchemy import DateTime, NullPool, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.shared.config import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            future=True,
            poolclass=NullPool,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


class Base(DeclarativeBase):
    pass


class BaseTable(Base):
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )


async def set_tenant_context(session: AsyncSession, tenant_id: UUID) -> None:
    # Set the local Postgres RLS setting for this transaction
    await session.execute(
        text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
        {"tenant_id": str(tenant_id)},
    )


async def get_privileged_session(
    factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> AsyncIterator[AsyncSession]:
    async with factory() as session:
        yield session


async def get_tenant_session(
    tenant_id: UUID,
    factory: async_sessionmaker[AsyncSession] | None = None,
) -> AsyncIterator[AsyncSession]:
    session_factory = factory or get_session_factory()
    async with session_factory() as session, session.begin():
        await set_tenant_context(session, tenant_id)
        yield session

