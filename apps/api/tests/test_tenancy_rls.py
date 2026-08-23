from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.internal.models import User, UserRole
from app.modules.identity.internal.repository import TenantRepository, UserRepository
from app.shared.db import set_tenant_context


@pytest.mark.asyncio
async def test_postgres_rls_tenant_isolation(
    db_session: AsyncSession,
) -> None:
    # 1. Seed Tenant A and Tenant B using privileged session
    tenant_repo = TenantRepository(db_session)
    tenant_a = await tenant_repo.create(name="Tenant Alpha", slug=f"alpha-{uuid4().hex[:6]}")
    tenant_b = await tenant_repo.create(name="Tenant Beta", slug=f"beta-{uuid4().hex[:6]}")

    user_repo = UserRepository(db_session)
    user_a = await user_repo.create(
        tenant_id=tenant_a.id,
        email="user@alpha.com",
        name="Alpha User",
        role=UserRole.STUDENT,
    )
    user_b = await user_repo.create(
        tenant_id=tenant_b.id,
        email="user@beta.com",
        name="Beta User",
        role=UserRole.STUDENT,
    )
    await db_session.commit()

    # 2. Query within Tenant A's RLS Context under non-superuser role
    await db_session.execute(text("SET ROLE learnloop_app;"))
    await set_tenant_context(db_session, tenant_a.id)

    stmt = select(User)
    result_a = await db_session.execute(stmt)
    users_in_a = list(result_a.scalars().all())

    # Assert: Tenant A session can ONLY see Tenant A user
    assert len(users_in_a) == 1
    assert users_in_a[0].id == user_a.id
    assert users_in_a[0].tenant_id == tenant_a.id

    # Direct query by Tenant B's ID within Tenant A's context returns None
    stmt_b = select(User).where(User.id == user_b.id)
    result_b_in_a = await db_session.execute(stmt_b)
    assert result_b_in_a.scalar_one_or_none() is None

    # 3. Query within Tenant B's RLS Context
    await set_tenant_context(db_session, tenant_b.id)
    result_b = await db_session.execute(select(User))
    users_in_b = list(result_b.scalars().all())

    assert len(users_in_b) == 1
    assert users_in_b[0].id == user_b.id
    assert users_in_b[0].tenant_id == tenant_b.id

    # Reset role
    await db_session.execute(text("RESET ROLE;"))


@pytest.mark.asyncio
async def test_cross_tenant_access_blocked_via_jwt_and_rls(
    client: AsyncClient,
) -> None:
    # 1. Register Org A and Org B
    reg_a = await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": "Org Alpha Corp",
            "name": "Alice Alpha",
            "email": "alice@alpha-corp.com",
            "password": "Password12345!",
        },
    )
    assert reg_a.status_code == 201
    token_a = reg_a.json()["tokens"]["access_token"]
    tenant_a_id = reg_a.json()["tenant"]["id"]

    reg_b = await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": "Org Beta Corp",
            "name": "Bob Beta",
            "email": "bob@beta-corp.com",
            "password": "Password12345!",
        },
    )
    assert reg_b.status_code == 201
    tenant_b_id = reg_b.json()["tenant"]["id"]

    assert tenant_a_id != tenant_b_id

    # 2. Alice calls /me with her token -> receives Org Alpha data
    me_a = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert me_a.status_code == 200
    assert me_a.json()["tenant"]["name"] == "Org Alpha Corp"
    assert me_a.json()["user"]["email"] == "alice@alpha-corp.com"
