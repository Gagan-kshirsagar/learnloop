import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_tutor_postgres_rls_isolation(client: AsyncClient) -> None:
    # 1. Register Tenant A (Harvard)
    res_a = await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": f"Harvard-{uuid.uuid4().hex[:6]}",
            "name": "Prof. Harvard",
            "email": f"prof-{uuid.uuid4().hex[:6]}@harvard.edu",
            "password": "Password123!",
        },
    )
    assert res_a.status_code == 201
    headers_a = {"Authorization": f"Bearer {res_a.json()['tokens']['access_token']}"}

    # 2. Register Tenant B (Yale)
    res_b = await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": f"Yale-{uuid.uuid4().hex[:6]}",
            "name": "Prof. Yale",
            "email": f"prof-{uuid.uuid4().hex[:6]}@yale.edu",
            "password": "Password123!",
        },
    )
    assert res_b.status_code == 201
    headers_b = {"Authorization": f"Bearer {res_b.json()['tokens']['access_token']}"}

    # 3. Create and Ingest Lesson in Tenant A
    course_a = await client.post(
        "/api/v1/catalog/courses",
        headers=headers_a,
        json={"title": "CS50", "description": "Harvard Course"},
    )
    course_a_id = course_a.json()["id"]

    mod_a = await client.post(
        "/api/v1/catalog/modules",
        headers=headers_a,
        json={"course_id": course_a_id, "title": "Module A"},
    )
    mod_a_id = mod_a.json()["id"]

    les_a = await client.post(
        "/api/v1/catalog/lessons",
        headers=headers_a,
        json={
            "module_id": mod_a_id,
            "title": "Confidential Research",
            "content_md": (
                "# Confidential Research\n\nProprietary formula X=42 exclusively at Harvard."
            ),
        },
    )
    lesson_a_id = les_a.json()["id"]

    # Ingest into Tenant A pgvector
    ingest_a = await client.post(f"/api/v1/tutor/lessons/{lesson_a_id}/ingest", headers=headers_a)
    assert ingest_a.status_code == 200
    assert ingest_a.json()["chunks_created"] > 0

    # 4. Tenant A asks about "Proprietary formula" -> Can retrieve and cite
    ask_a = await client.post(
        "/api/v1/tutor/ask",
        headers=headers_a,
        json={"question": "# Confidential Research"},
    )
    assert ask_a.status_code == 200
    assert ask_a.json()["used_context"] is True
    assert len(ask_a.json()["citations"]) > 0

    # 5. Tenant B asks about "Proprietary formula" -> RLS BLOCKS cross-tenant chunk access
    ask_b = await client.post(
        "/api/v1/tutor/ask",
        headers=headers_b,
        json={"question": "# Confidential Research"},
    )
    assert ask_b.status_code == 200
    # Must decline and NOT cite Tenant A's private chunks!
    assert ask_b.json()["used_context"] is False
    assert ask_b.json()["citations"] == []
