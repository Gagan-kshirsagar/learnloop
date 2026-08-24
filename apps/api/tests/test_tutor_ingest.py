import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_lesson_ingestion_and_idempotency(client: AsyncClient) -> None:
    # 1. Register instructor
    inst_res = await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": f"Stanford-{uuid.uuid4().hex[:6]}",
            "name": "Prof. Ng",
            "email": f"ng-{uuid.uuid4().hex[:6]}@stanford.edu",
            "password": "Password123!",
        },
    )
    assert inst_res.status_code == 201
    headers = {"Authorization": f"Bearer {inst_res.json()['tokens']['access_token']}"}

    # 2. Create course, module, lesson
    course_res = await client.post(
        "/api/v1/catalog/courses",
        headers=headers,
        json={"title": "Deep Learning", "description": "Neural Nets"},
    )
    course_id = course_res.json()["id"]

    mod_res = await client.post(
        "/api/v1/catalog/modules",
        headers=headers,
        json={"course_id": course_id, "title": "Module 1"},
    )
    mod_id = mod_res.json()["id"]

    long_content = "\n\n".join(
        [
            f"### Section {i}\nBackpropagation calculates the gradient of the loss function "
            f"with respect to the weights of the network {i}."
            for i in range(15)
        ]
    )

    les_res = await client.post(
        "/api/v1/catalog/lessons",
        headers=headers,
        json={"module_id": mod_id, "title": "Backpropagation", "content_md": long_content},
    )
    lesson_id = les_res.json()["id"]

    # 3. Ingest lesson into pgvector
    ingest1 = await client.post(f"/api/v1/tutor/lessons/{lesson_id}/ingest", headers=headers)
    assert ingest1.status_code == 200
    data1 = ingest1.json()
    assert data1["chunks_created"] > 0
    assert data1["total_tokens"] > 0
    initial_chunks = data1["chunks_created"]

    # 4. Re-ingest the SAME lesson (Idempotency test)
    ingest2 = await client.post(f"/api/v1/tutor/lessons/{lesson_id}/ingest", headers=headers)
    assert ingest2.status_code == 200
    data2 = ingest2.json()
    assert data2["chunks_created"] == initial_chunks  # Chunks are replaced, not duplicated!

    # 5. Course batch ingestion
    course_ingest = await client.post(f"/api/v1/tutor/courses/{course_id}/ingest", headers=headers)
    assert course_ingest.status_code == 200
    c_data = course_ingest.json()
    assert c_data["lessons_ingested"] == 1
    assert c_data["total_chunks"] == initial_chunks
