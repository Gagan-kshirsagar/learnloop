import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_postgres_rls_catalog_isolation(client: AsyncClient) -> None:
    # 1. Register Tenant A (Stanford)
    res_a = await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": "Stanford University",
            "name": "Prof. A",
            "email": "prof_a@stanford.edu",
            "password": "PasswordA123!",
        },
    )
    assert res_a.status_code == 201
    headers_a = {"Authorization": f"Bearer {res_a.json()['tokens']['access_token']}"}

    # 2. Register Tenant B (Berkeley)
    res_b = await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": "UC Berkeley",
            "name": "Prof. B",
            "email": "prof_b@berkeley.edu",
            "password": "PasswordB123!",
        },
    )
    assert res_b.status_code == 201
    headers_b = {"Authorization": f"Bearer {res_b.json()['tokens']['access_token']}"}

    # 3. Create Course A in Tenant A
    course_a_res = await client.post(
        "/api/v1/catalog/courses",
        headers=headers_a,
        json={"title": "CS106B: Programming Abstractions", "description": "Stanford C++"},
    )
    assert course_a_res.status_code == 201
    course_a_id = course_a_res.json()["id"]

    # 4. Create Course B in Tenant B
    course_b_res = await client.post(
        "/api/v1/catalog/courses",
        headers=headers_b,
        json={"title": "CS61A: Structure and Interpretation", "description": "Berkeley Python"},
    )
    assert course_b_res.status_code == 201
    course_b_id = course_b_res.json()["id"]

    # 5. Create Module & Lesson in Tenant B
    mod_b_res = await client.post(
        "/api/v1/catalog/modules",
        headers=headers_b,
        json={"course_id": course_b_id, "title": "Higher-Order Functions"},
    )
    mod_b_id = mod_b_res.json()["id"]

    les_b_res = await client.post(
        "/api/v1/catalog/lessons",
        headers=headers_b,
        json={
            "module_id": mod_b_id,
            "title": "Lambda Expressions",
            "content_md": "Lambdas in Scheme and Python",
        },
    )
    les_b_id = les_b_res.json()["id"]

    # 6. Tenant A lists courses -> MUST ONLY see Course A, never Course B
    list_a_res = await client.get("/api/v1/catalog/courses", headers=headers_a)
    assert list_a_res.status_code == 200
    courses_a = list_a_res.json()
    assert len(courses_a) == 1
    assert courses_a[0]["id"] == course_a_id

    # 7. Tenant A attempts direct cross-tenant access to Course B -> 404
    get_b_from_a = await client.get(f"/api/v1/catalog/courses/{course_b_id}", headers=headers_a)
    assert get_b_from_a.status_code == 404

    # 8. Tenant A attempts cross-tenant access to Lesson B -> 404
    get_les_b_from_a = await client.get(f"/api/v1/catalog/lessons/{les_b_id}", headers=headers_a)
    assert get_les_b_from_a.status_code == 404

    # 9. Tenant A attempts cross-tenant mutation on Course B -> 404
    patch_b_from_a = await client.patch(
        f"/api/v1/catalog/courses/{course_b_id}",
        headers=headers_a,
        json={"title": "Hacked Title"},
    )
    assert patch_b_from_a.status_code == 404

    # 10. Tenant A attempts cross-tenant deletion of Course B -> 404
    del_b_from_a = await client.delete(
        f"/api/v1/catalog/courses/{course_b_id}",
        headers=headers_a,
    )
    assert del_b_from_a.status_code == 404
