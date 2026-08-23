import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_learning_postgres_rls_isolation(client: AsyncClient) -> None:
    # 1. Register Tenant A (Harvard)
    res_a = await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": "Harvard",
            "name": "Prof. Harvard",
            "email": "prof@harvard.edu",
            "password": "PasswordA123!",
        },
    )
    headers_a = {"Authorization": f"Bearer {res_a.json()['tokens']['access_token']}"}

    # 2. Register Tenant B (Yale)
    res_b = await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": "Yale",
            "name": "Prof. Yale",
            "email": "prof@yale.edu",
            "password": "PasswordB123!",
        },
    )
    headers_b = {"Authorization": f"Bearer {res_b.json()['tokens']['access_token']}"}

    # 3. Create Course A in Tenant A
    course_a = await client.post(
        "/api/v1/catalog/courses",
        headers=headers_a,
        json={"title": "CS50", "description": "Intro to Computer Science"},
    )
    course_a_id = course_a.json()["id"]

    # 4. Create Course B in Tenant B
    course_b = await client.post(
        "/api/v1/catalog/courses",
        headers=headers_b,
        json={"title": "CPSC 201", "description": "Intro to CS at Yale"},
    )
    course_b_id = course_b.json()["id"]

    # 5. Enroll Prof A in Course A
    enroll_a = await client.post(
        f"/api/v1/learning/courses/{course_a_id}/enroll",
        headers=headers_a,
    )
    assert enroll_a.status_code == 201

    # 6. Enroll Prof B in Course B
    enroll_b = await client.post(
        f"/api/v1/learning/courses/{course_b_id}/enroll",
        headers=headers_b,
    )
    assert enroll_b.status_code == 201

    # 7. Tenant A calls /me/enrollments -> MUST ONLY see Course A
    my_enr_a = await client.get("/api/v1/learning/me/enrollments", headers=headers_a)
    assert my_enr_a.status_code == 200
    courses_a = my_enr_a.json()
    assert len(courses_a) == 1
    assert courses_a[0]["course_id"] == course_a_id

    # 8. Tenant A attempts to enroll in Course B -> 404
    # (Course B does not exist in Tenant A RLS scope)
    cross_enroll = await client.post(
        f"/api/v1/learning/courses/{course_b_id}/enroll",
        headers=headers_a,
    )
    assert cross_enroll.status_code == 404
