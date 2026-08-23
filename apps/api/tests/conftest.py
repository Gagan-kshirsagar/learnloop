import os
from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.main import app
from app.shared.config import Settings, get_settings
from app.shared.db import Base, get_session_factory

TEST_DATABASE_URL = os.environ.get(
    "LEARNLOOP_TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/learnloop_test",
)


def get_test_settings() -> Settings:
    return Settings(
        database_url=TEST_DATABASE_URL,
        jwt_secret_key="test-jwt-secret-key",
        auth_provider="jwt",
    )


@pytest_asyncio.fixture(scope="function")
async def test_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        poolclass=NullPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        for table in ["users", "courses", "modules", "lessons"]:
            await conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))
            await conn.execute(text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;"))
            await conn.execute(text(f"DROP POLICY IF EXISTS tenant_isolation ON {table};"))
            await conn.execute(
                text(
                    f"CREATE POLICY tenant_isolation ON {table} "
                    "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);"
                )
            )

        await conn.execute(
            text(
                "DO $$ BEGIN "
                "IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'learnloop_app') THEN "
                "CREATE ROLE learnloop_app; "
                "END IF; "
                "END $$;"
            )
        )
        await conn.execute(text("GRANT ALL ON ALL TABLES IN SCHEMA public TO learnloop_app;"))
        await conn.execute(text("GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO learnloop_app;"))
    yield engine
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM lessons;"))
        await conn.execute(text("DELETE FROM modules;"))
        await conn.execute(text("DELETE FROM courses;"))
        await conn.execute(text("DELETE FROM users;"))
        await conn.execute(text("DELETE FROM tenants;"))
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with factory() as session:
        yield session
        async with test_engine.begin() as conn:
            await conn.execute(text("DELETE FROM lessons;"))
            await conn.execute(text("DELETE FROM modules;"))
            await conn.execute(text("DELETE FROM courses;"))
            await conn.execute(text("DELETE FROM users;"))
            await conn.execute(text("DELETE FROM tenants;"))


@pytest_asyncio.fixture(scope="function")
async def client(test_engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_settings] = get_test_settings

    test_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    app.dependency_overrides[get_session_factory] = lambda: test_factory

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
