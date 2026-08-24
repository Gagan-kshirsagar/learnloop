import uuid
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.internal.auth_provider import JwtAuthProvider


async def _create_student_token(
    db_session: AsyncSession,
    tenant_id: UUID,
    email: str = "student@example.com",
) -> str:
    student_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO users (id, tenant_id, email, name, role, status, created_at) "
            "VALUES (:id, :tenant_id, :email, 'Student Learner', 'student', 'active', now())"
        ),
        {"id": student_id, "tenant_id": tenant_id, "email": email},
    )
    await db_session.commit()

    jwt_provider = JwtAuthProvider()
    return jwt_provider.create_access_token(
        user_id=student_id,
        tenant_id=tenant_id,
        role="student",
    )


@pytest.mark.asyncio
async def test_tutor_rag_grounded_answer_and_citations(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    # 1. Register instructor & create lesson
    inst_res = await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": f"MIT-{uuid.uuid4().hex[:6]}",
            "name": "Prof. Sussman",
            "email": f"sussman-{uuid.uuid4().hex[:6]}@mit.edu",
            "password": "Password123!",
        },
    )
    assert inst_res.status_code == 201
    tenant_id = UUID(inst_res.json()["tenant"]["id"])
    inst_headers = {"Authorization": f"Bearer {inst_res.json()['tokens']['access_token']}"}

    course_res = await client.post(
        "/api/v1/catalog/courses",
        headers=inst_headers,
        json={"title": "SICP", "description": "Structure and Interpretation"},
    )
    course_id = course_res.json()["id"]

    mod_res = await client.post(
        "/api/v1/catalog/modules",
        headers=inst_headers,
        json={"course_id": course_id, "title": "Module 1"},
    )
    mod_id = mod_res.json()["id"]

    lesson_content = (
        "# Recursion and Call Stacks\n\n"
        "A recursive function solves problems by breaking them down into base cases "
        "and recursive steps.\n\n"
        "Every recursive call creates a new stack frame in memory storing local parameters."
    )
    les_res = await client.post(
        "/api/v1/catalog/lessons",
        headers=inst_headers,
        json={"module_id": mod_id, "title": "Recursion", "content_md": lesson_content},
    )
    lesson_id = les_res.json()["id"]

    # Ingest lesson
    await client.post(f"/api/v1/tutor/lessons/{lesson_id}/ingest", headers=inst_headers)

    # 2. Student in same tenant asks in-scope question
    stud_token = await _create_student_token(
        db_session,
        tenant_id,
        email=f"learner-{uuid.uuid4().hex[:6]}@mit.edu",
    )
    stud_headers = {"Authorization": f"Bearer {stud_token}"}

    # Query with exact lesson context match
    ask_res = await client.post(
        "/api/v1/tutor/ask",
        headers=stud_headers,
        json={
            "question": "# Recursion and Call Stacks",
            "lesson_id": lesson_id,
        },
    )
    assert ask_res.status_code == 200
    data = ask_res.json()
    assert data["used_context"] is True
    assert len(data["citations"]) > 0
    assert data["citations"][0]["lesson_id"] == lesson_id
    assert "Recursion" in data["answer"]


@pytest.mark.asyncio
async def test_tutor_rag_out_of_scope_decline(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    # 1. Register instructor
    inst_res = await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": f"Berkeley-{uuid.uuid4().hex[:6]}",
            "name": "Prof. Russell",
            "email": f"russell-{uuid.uuid4().hex[:6]}@berkeley.edu",
            "password": "Password123!",
        },
    )
    tenant_id = UUID(inst_res.json()["tenant"]["id"])

    stud_token = await _create_student_token(
        db_session,
        tenant_id,
        email=f"student-{uuid.uuid4().hex[:6]}@berkeley.edu",
    )
    stud_headers = {"Authorization": f"Bearer {stud_token}"}

    # 2. Ask question with no chunks ingested in the tenant
    ask_res = await client.post(
        "/api/v1/tutor/ask",
        headers=stud_headers,
        json={"question": "What is the capital of France?"},
    )
    assert ask_res.status_code == 200
    data = ask_res.json()
    assert data["used_context"] is False
    assert data["citations"] == []
    assert "isn't covered" in data["answer"]


@pytest.mark.asyncio
async def test_tutor_unauthenticated_forbidden(client: AsyncClient) -> None:
    res = await client.post(
        "/api/v1/tutor/ask",
        json={"question": "How to learn python?"},
    )
    assert res.status_code == 401
