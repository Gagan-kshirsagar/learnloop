import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_author_course_module_lesson_crud_and_reorder(client: AsyncClient) -> None:
    # 1. Register instructor
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": "MIT EECS",
            "name": "Prof. Strang",
            "email": "strang@mit.edu",
            "password": "Password123!",
        },
    )
    assert reg_res.status_code == 201
    auth_headers = {"Authorization": f"Bearer {reg_res.json()['tokens']['access_token']}"}

    # 2. Create course
    course_res = await client.post(
        "/api/v1/catalog/courses",
        headers=auth_headers,
        json={
            "title": "Introduction to Algorithms",
            "description": "Fundamental data structures and sorting algorithms",
        },
    )
    assert course_res.status_code == 201
    course_data = course_res.json()
    course_id = course_data["id"]
    assert course_data["title"] == "Introduction to Algorithms"
    assert course_data["slug"] == "introduction-to-algorithms"
    assert course_data["status"] == "draft"

    # 3. Create modules
    m1_res = await client.post(
        "/api/v1/catalog/modules",
        headers=auth_headers,
        json={"course_id": course_id, "title": "Module 1: Foundations"},
    )
    assert m1_res.status_code == 201
    m1_id = m1_res.json()["id"]
    assert m1_res.json()["position"] == 0

    m2_res = await client.post(
        "/api/v1/catalog/modules",
        headers=auth_headers,
        json={"course_id": course_id, "title": "Module 2: Graph Algorithms"},
    )
    assert m2_res.status_code == 201
    m2_id = m2_res.json()["id"]
    assert m2_res.json()["position"] == 1

    # 4. Reorder modules (put m2 first)
    reorder_mod_res = await client.post(
        "/api/v1/catalog/modules/reorder",
        headers=auth_headers,
        json={"course_id": course_id, "ordered_module_ids": [m2_id, m1_id]},
    )
    assert reorder_mod_res.status_code == 200
    mods = reorder_mod_res.json()
    assert mods[0]["id"] == m2_id
    assert mods[0]["position"] == 0
    assert mods[1]["id"] == m1_id
    assert mods[1]["position"] == 1

    # 5. Create lessons in module 1
    l1_res = await client.post(
        "/api/v1/catalog/lessons",
        headers=auth_headers,
        json={
            "module_id": m1_id,
            "title": "Asymptotic Analysis",
            "content_md": "# Big O Notation\nUnderstanding time complexity.",
        },
    )
    assert l1_res.status_code == 201
    l1_id = l1_res.json()["id"]
    assert l1_res.json()["position"] == 0

    l2_res = await client.post(
        "/api/v1/catalog/lessons",
        headers=auth_headers,
        json={
            "module_id": m1_id,
            "title": "Divide and Conquer",
            "content_md": "# Divide and Conquer\nBinary Search and Merge Sort.",
        },
    )
    assert l2_res.status_code == 201
    l2_id = l2_res.json()["id"]
    assert l2_res.json()["position"] == 1

    # 6. Reorder lessons
    reorder_les_res = await client.post(
        "/api/v1/catalog/lessons/reorder",
        headers=auth_headers,
        json={"module_id": m1_id, "ordered_lesson_ids": [l2_id, l1_id]},
    )
    assert reorder_les_res.status_code == 200
    lessons = reorder_les_res.json()
    assert lessons[0]["id"] == l2_id
    assert lessons[0]["position"] == 0
    assert lessons[1]["id"] == l1_id
    assert lessons[1]["position"] == 1

    # 7. Get full course hierarchy
    course_detail_res = await client.get(
        f"/api/v1/catalog/courses/{course_id}",
        headers=auth_headers,
    )
    assert course_detail_res.status_code == 200
    detail = course_detail_res.json()
    assert len(detail["modules"]) == 2


@pytest.mark.asyncio
async def test_learner_visibility_gating(client: AsyncClient) -> None:
    # 1. Register instructor and create a draft course
    inst_res = await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": "Stanford CS",
            "name": "Prof. Knuth",
            "email": "knuth@stanford.edu",
            "password": "Password123!",
        },
    )
    inst_headers = {"Authorization": f"Bearer {inst_res.json()['tokens']['access_token']}"}

    course_res = await client.post(
        "/api/v1/catalog/courses",
        headers=inst_headers,
        json={"title": "Compilers & Parsers", "description": "AST and bytecode generation"},
    )
    course_id = course_res.json()["id"]

    mod_res = await client.post(
        "/api/v1/catalog/modules",
        headers=inst_headers,
        json={"course_id": course_id, "title": "Lexing and Parsing"},
    )
    mod_id = mod_res.json()["id"]

    les_res = await client.post(
        "/api/v1/catalog/lessons",
        headers=inst_headers,
        json={
            "module_id": mod_id,
            "title": "Recursive Descent Parsers",
            "content_md": "# Recursive Descent\nBuilding an AST in Python.",
        },
    )
    lesson_id = les_res.json()["id"]

    # 2. Create guest learner
    guest_res = await client.post("/api/v1/auth/guest")
    guest_headers = {"Authorization": f"Bearer {guest_res.json()['tokens']['access_token']}"}

    # 3. Learner tries to list courses -> draft course is NOT returned
    courses_res = await client.get("/api/v1/catalog/courses", headers=guest_headers)
    assert courses_res.status_code == 200
    assert len(courses_res.json()) == 0

    # 4. Learner tries to get course directly -> 404
    get_res = await client.get(f"/api/v1/catalog/courses/{course_id}", headers=guest_headers)
    assert get_res.status_code == 404

    # 5. Instructor publishes course
    pub_res = await client.post(
        f"/api/v1/catalog/courses/{course_id}/publish",
        headers=inst_headers,
        json={"status": "published"},
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "published"

    # 6. Instructor sees published course
    inst_courses_res = await client.get("/api/v1/catalog/courses", headers=inst_headers)
    assert len(inst_courses_res.json()) == 1

    # 7. Learner gets full lesson content
    les_detail_res = await client.get(f"/api/v1/catalog/lessons/{lesson_id}", headers=inst_headers)
    assert les_detail_res.status_code == 200
    assert "Recursive Descent" in les_detail_res.json()["content_md"]


@pytest.mark.asyncio
async def test_rbac_student_cannot_author(client: AsyncClient) -> None:
    # 1. Create a guest student session
    guest_res = await client.post("/api/v1/auth/guest")
    assert guest_res.status_code == 201
    guest_headers = {"Authorization": f"Bearer {guest_res.json()['tokens']['access_token']}"}

    # 2. Attempt to create course -> 403 Forbidden
    post_res = await client.post(
        "/api/v1/catalog/courses",
        headers=guest_headers,
        json={"title": "Hacked Course"},
    )
    assert post_res.status_code == 403
    assert "Insufficient permissions" in post_res.json()["detail"]
