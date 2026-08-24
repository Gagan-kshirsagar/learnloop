import json
import uuid
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.internal.auth_provider import JwtAuthProvider


async def _create_user(
    client: AsyncClient,
    email: str,
    org_name: str = "MIT Labs",
    name: str = "Prof. Alice",
) -> tuple[UUID, UUID, str]:
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": org_name,
            "name": name,
            "email": email,
            "password": "Password123!",
        },
    )
    data = res.json()
    return (
        UUID(data["user"]["id"]),
        UUID(data["tenant"]["id"]),
        data["tokens"]["access_token"],
    )


async def _create_student_in_tenant(
    db_session: AsyncSession,
    tenant_id: UUID,
    email: str = "student@example.com",
    name: str = "Student Learner",
) -> tuple[UUID, str]:
    student_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO users (id, tenant_id, email, name, role, status, created_at) "
            "VALUES (:id, :tenant_id, :email, :name, 'student', 'active', now())"
        ),
        {"id": student_id, "tenant_id": tenant_id, "email": email, "name": name},
    )
    await db_session.commit()

    jwt_provider = JwtAuthProvider()
    token = jwt_provider.create_access_token(
        user_id=student_id,
        tenant_id=tenant_id,
        role="student",
    )
    return student_id, token


def _parse_sse_events(raw_body: str) -> list[dict[str, str]]:
    events = []
    blocks = raw_body.strip().split("\n\n")
    for block in blocks:
        if not block.strip():
            continue
        event_name = "message"
        data_str = ""
        for line in block.splitlines():
            if line.startswith("event: "):
                event_name = line[7:].strip()
            elif line.startswith("data: "):
                data_str = line[6:].strip()
        if data_str:
            events.append({"event": event_name, "data": data_str})
    return events


@pytest.mark.asyncio
async def test_tutor_stream_sequence_and_persistence(
    client: AsyncClient,
) -> None:
    _, _, inst_token = await _create_user(client, "prof@mit.edu", org_name="MIT")
    headers = {"Authorization": f"Bearer {inst_token}"}

    # 1. Create course, module, lesson
    c_res = await client.post(
        "/api/v1/catalog/courses",
        headers=headers,
        json={"title": "Python 101", "description": "Intro"},
    )
    course_id = c_res.json()["id"]

    m_res = await client.post(
        "/api/v1/catalog/modules",
        headers=headers,
        json={"course_id": course_id, "title": "Module 1"},
    )
    mod_id = m_res.json()["id"]

    content = """# Dynamic Typing in Python

Python is dynamically typed. Variables can hold any object type without static declaration.
Dynamic typing allows rapid prototyping and flexibility."""
    l_res = await client.post(
        "/api/v1/catalog/lessons",
        headers=headers,
        json={"module_id": mod_id, "title": "Dynamic Typing", "content_md": content},
    )
    lesson_id = l_res.json()["id"]

    # 2. Ingest lesson into vector store
    ingest_res = await client.post(
        f"/api/v1/tutor/lessons/{lesson_id}/ingest",
        headers=headers,
    )
    assert ingest_res.status_code == 200

    # 3. Stream question
    stream_res = await client.post(
        "/api/v1/tutor/stream",
        headers=headers,
        json={"question": "What is dynamic typing", "lesson_id": lesson_id},
    )
    assert stream_res.status_code == 200
    assert "text/event-stream" in stream_res.headers["content-type"]

    events = _parse_sse_events(stream_res.text)
    event_names = [e["event"] for e in events]

    assert "token" in event_names
    assert "citations" in event_names
    assert "done" in event_names

    # Check citations payload
    cit_event = next(e for e in events if e["event"] == "citations")
    cit_data = json.loads(cit_event["data"])
    assert len(cit_data["citations"]) > 0
    assert cit_data["citations"][0]["ordinal"] == 0

    # Check done payload
    done_event = next(e for e in events if e["event"] == "done")
    done_data = json.loads(done_event["data"])
    session_id = done_data["session_id"]
    assert session_id is not None

    # 4. Verify session and messages are persisted in DB
    session_detail_res = await client.get(
        f"/api/v1/tutor/sessions/{session_id}",
        headers=headers,
    )
    assert session_detail_res.status_code == 200
    detail = session_detail_res.json()
    assert detail["session"]["id"] == session_id
    assert len(detail["messages"]) == 2
    assert detail["messages"][0]["role"] == "user"
    assert "What is dynamic typing" in detail["messages"][0]["content"]
    assert detail["messages"][1]["role"] == "assistant"
    assert "Based on the lesson material" in detail["messages"][1]["content"]


@pytest.mark.asyncio
async def test_tutor_stream_multi_turn_memory(
    client: AsyncClient,
) -> None:
    _, _, token = await _create_user(client, "learner@stanford.edu", org_name="Stanford")
    headers = {"Authorization": f"Bearer {token}"}

    c_res = await client.post(
        "/api/v1/catalog/courses",
        headers=headers,
        json={"title": "Systems", "description": "CS"},
    )
    course_id = c_res.json()["id"]

    m_res = await client.post(
        "/api/v1/catalog/modules",
        headers=headers,
        json={"course_id": course_id, "title": "Caching"},
    )
    mod_id = m_res.json()["id"]

    content = """# LRU Cache Design

An LRU Cache evicts the least recently used item when reaching capacity.
Hash maps provide O(1) lookups while doubly-linked lists provide O(1) node removals."""
    l_res = await client.post(
        "/api/v1/catalog/lessons",
        headers=headers,
        json={"module_id": mod_id, "title": "LRU Cache", "content_md": content},
    )
    lesson_id = l_res.json()["id"]

    await client.post(f"/api/v1/tutor/lessons/{lesson_id}/ingest", headers=headers)

    # Turn 1
    t1_res = await client.post(
        "/api/v1/tutor/stream",
        headers=headers,
        json={"question": "Explain LRU cache eviction", "lesson_id": lesson_id},
    )
    t1_events = _parse_sse_events(t1_res.text)
    done_event = next(e for e in t1_events if e["event"] == "done")
    session_id = json.loads(done_event["data"])["session_id"]

    # Turn 2 in same session
    t2_res = await client.post(
        "/api/v1/tutor/stream",
        headers=headers,
        json={
            "session_id": session_id,
            "question": "How do hash maps help with O(1) lookups?",
            "lesson_id": lesson_id,
        },
    )
    t2_events = _parse_sse_events(t2_res.text)
    assert any(e["event"] == "done" for e in t2_events)

    # Verify session detail contains all 4 messages
    detail_res = await client.get(
        f"/api/v1/tutor/sessions/{session_id}",
        headers=headers,
    )
    detail = detail_res.json()
    assert len(detail["messages"]) == 4
    roles = [m["role"] for m in detail["messages"]]
    assert roles == ["user", "assistant", "user", "assistant"]


@pytest.mark.asyncio
async def test_tutor_stream_out_of_scope_decline(
    client: AsyncClient,
) -> None:
    _, _, token = await _create_user(client, "student@oxford.ac.uk", org_name="Oxford")
    headers = {"Authorization": f"Bearer {token}"}

    c_res = await client.post(
        "/api/v1/catalog/courses",
        headers=headers,
        json={"title": "Biology", "description": "Bio"},
    )
    course_id = c_res.json()["id"]

    m_res = await client.post(
        "/api/v1/catalog/modules",
        headers=headers,
        json={"course_id": course_id, "title": "Cells"},
    )
    mod_id = m_res.json()["id"]

    content = "# Mitochondria\nMitochondria generate ATP for cellular metabolism."
    l_res = await client.post(
        "/api/v1/catalog/lessons",
        headers=headers,
        json={"module_id": mod_id, "title": "Mitochondria", "content_md": content},
    )
    lesson_id = l_res.json()["id"]
    await client.post(f"/api/v1/tutor/lessons/{lesson_id}/ingest", headers=headers)

    # Out-of-scope question
    stream_res = await client.post(
        "/api/v1/tutor/stream",
        headers=headers,
        json={"question": "What is quantum gravity in physics?", "lesson_id": lesson_id},
    )
    events = _parse_sse_events(stream_res.text)

    tokens = [json.loads(e["data"])["text"] for e in events if e["event"] == "token"]
    full_text = "".join(tokens)
    assert "That isn't covered in this lesson." in full_text

    cit_event = next(e for e in events if e["event"] == "citations")
    assert json.loads(cit_event["data"])["citations"] == []


@pytest.mark.asyncio
async def test_tutor_stream_ownership_and_tenancy(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    # User A and User B in same tenant
    _, tenant_id, token_a = await _create_user(
        client, "alice@cambridge.ac.uk", org_name="Cambridge"
    )
    _, token_b = await _create_student_in_tenant(db_session, tenant_id, email="bob@cambridge.ac.uk")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates a chat session via stream
    res_a = await client.post(
        "/api/v1/tutor/stream",
        headers=headers_a,
        json={"question": "Tell me about mathematics"},
    )
    events_a = _parse_sse_events(res_a.text)
    done_event = next(e for e in events_a if e["event"] == "done")
    session_id_a = json.loads(done_event["data"])["session_id"]

    # User B tries to read User A's session -> 403 Forbidden
    res_b_read = await client.get(
        f"/api/v1/tutor/sessions/{session_id_a}",
        headers=headers_b,
    )
    assert res_b_read.status_code == 403

    # User B tries to delete User A's session -> 403 Forbidden
    res_b_delete = await client.delete(
        f"/api/v1/tutor/sessions/{session_id_a}",
        headers=headers_b,
    )
    assert res_b_delete.status_code == 403

    # User B tries to post message to User A's session -> stream error event
    res_b_stream = await client.post(
        "/api/v1/tutor/stream",
        headers=headers_b,
        json={"session_id": session_id_a, "question": "Hacking session"},
    )
    events_b = _parse_sse_events(res_b_stream.text)
    assert any(e["event"] == "error" for e in events_b)
