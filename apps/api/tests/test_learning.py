import asyncio
import uuid
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.internal.auth_provider import JwtAuthProvider


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


@pytest.mark.asyncio
async def test_enrollment_and_my_learning(client: AsyncClient, db_session: AsyncSession) -> None:
    # 1. Register instructor and create a course with a lesson
    inst_res = await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": f"Caltech-{uuid.uuid4().hex[:6]}",
            "name": "Prof. Feynman",
            "email": f"feynman-{uuid.uuid4().hex[:6]}@caltech.edu",
            "password": "Password123!",
        },
    )
    assert inst_res.status_code == 201
    tenant_id = UUID(inst_res.json()["tenant"]["id"])
    inst_headers = {"Authorization": f"Bearer {inst_res.json()['tokens']['access_token']}"}

    course_res = await client.post(
        "/api/v1/catalog/courses",
        headers=inst_headers,
        json={"title": "Quantum Computation", "description": "Intro to Qubits"},
    )
    course_id = course_res.json()["id"]

    mod_res = await client.post(
        "/api/v1/catalog/modules",
        headers=inst_headers,
        json={"course_id": course_id, "title": "Module 1: Linear Algebra"},
    )
    mod_id = mod_res.json()["id"]

    les_res = await client.post(
        "/api/v1/catalog/lessons",
        headers=inst_headers,
        json={"module_id": mod_id, "title": "State Vectors", "content_md": "# Vectors"},
    )
    lesson_id = les_res.json()["id"]

    # 2. Create student in the same organization
    _, stud_token = await _create_student_in_tenant(
        db_session,
        tenant_id,
        email=f"bob-{uuid.uuid4().hex[:6]}@caltech.edu",
    )
    stud_headers = {"Authorization": f"Bearer {stud_token}"}

    # 3. Student enrolls in course
    enroll_res = await client.post(
        f"/api/v1/learning/courses/{course_id}/enroll",
        headers=stud_headers,
    )
    assert enroll_res.status_code == 201
    assert enroll_res.json()["status"] == "active"

    # 4. Student views my enrollments
    my_enr_res = await client.get("/api/v1/learning/me/enrollments", headers=stud_headers)
    assert my_enr_res.status_code == 200
    summaries = my_enr_res.json()
    assert len(summaries) == 1
    assert summaries[0]["course_title"] == "Quantum Computation"
    assert summaries[0]["total_lessons"] == 1
    assert summaries[0]["completed_lessons"] == 0

    # 5. Student marks lesson completed
    complete_res = await client.post(
        f"/api/v1/learning/lessons/{lesson_id}/complete",
        headers=stud_headers,
        json={"completed": True},
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["completed"] is True

    # 6. Progress percentage updates to 100%
    my_enr_res2 = await client.get("/api/v1/learning/me/enrollments", headers=stud_headers)
    assert my_enr_res2.json()[0]["completed_lessons"] == 1
    assert my_enr_res2.json()[0]["progress_percentage"] == 100


@pytest.mark.asyncio
async def test_exercise_authoring_and_learner_privacy(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    # 1. Register instructor
    inst_res = await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": f"Oxford-{uuid.uuid4().hex[:6]}",
            "name": "Prof. Turing",
            "email": f"turing-{uuid.uuid4().hex[:6]}@oxford.ac.uk",
            "password": "Password123!",
        },
    )
    assert inst_res.status_code == 201
    tenant_id = UUID(inst_res.json()["tenant"]["id"])
    inst_headers = {"Authorization": f"Bearer {inst_res.json()['tokens']['access_token']}"}

    course_res = await client.post(
        "/api/v1/catalog/courses",
        headers=inst_headers,
        json={"title": "Algorithms", "description": "Turing Machines"},
    )
    course_id = course_res.json()["id"]

    mod_res = await client.post(
        "/api/v1/catalog/modules",
        headers=inst_headers,
        json={"course_id": course_id, "title": "Module 1"},
    )
    mod_id = mod_res.json()["id"]

    les_res = await client.post(
        "/api/v1/catalog/lessons",
        headers=inst_headers,
        json={"module_id": mod_id, "title": "Turing Halting", "content_md": "# Halting"},
    )
    lesson_id = les_res.json()["id"]

    # 2. Instructor saves coding exercise with hidden tests
    hidden_tests = """
assert solve(5) == 25
assert solve(-2) == 4
__tests_passed = 2
__tests_total = 2
"""
    ex_res = await client.post(
        f"/api/v1/learning/lessons/{lesson_id}/exercise",
        headers=inst_headers,
        json={
            "prompt_md": "# Square the input\nWrite a function `solve(n)` that returns `n * n`.",
            "starter_code": "def solve(n):\n    pass\n",
            "tests_code": hidden_tests,
            "language": "python",
        },
    )
    assert ex_res.status_code == 200
    assert "tests_code" in ex_res.json()

    # 3. Learner reads exercise -> tests_code is STRIPPED
    _, stud_token = await _create_student_in_tenant(
        db_session,
        tenant_id,
        email=f"alice-{uuid.uuid4().hex[:6]}@oxford.ac.uk",
    )
    stud_headers = {"Authorization": f"Bearer {stud_token}"}

    learner_ex_res = await client.get(
        f"/api/v1/learning/lessons/{lesson_id}/exercise",
        headers=stud_headers,
    )
    assert learner_ex_res.status_code == 200
    learner_data = learner_ex_res.json()
    assert "Square the input" in learner_data["prompt_md"]
    assert "tests_code" not in learner_data  # Hidden test suite is NOT returned to learner!


@pytest.mark.asyncio
async def test_code_submission_execution_and_polling(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    # 1. Setup course, lesson, and exercise
    inst_res = await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": f"Princeton-{uuid.uuid4().hex[:6]}",
            "name": "Prof. Nash",
            "email": f"nash-{uuid.uuid4().hex[:6]}@princeton.edu",
            "password": "Password123!",
        },
    )
    assert inst_res.status_code == 201
    tenant_id = UUID(inst_res.json()["tenant"]["id"])
    inst_headers = {"Authorization": f"Bearer {inst_res.json()['tokens']['access_token']}"}

    course_res = await client.post(
        "/api/v1/catalog/courses",
        headers=inst_headers,
        json={"title": "Game Theory", "description": "Equilibrium"},
    )
    course_id = course_res.json()["id"]

    mod_res = await client.post(
        "/api/v1/catalog/modules",
        headers=inst_headers,
        json={"course_id": course_id, "title": "Module 1"},
    )
    mod_id = mod_res.json()["id"]

    les_res = await client.post(
        "/api/v1/catalog/lessons",
        headers=inst_headers,
        json={"module_id": mod_id, "title": "Payoff Matrices", "content_md": "# Matrices"},
    )
    lesson_id = les_res.json()["id"]

    tests_code = """
assert payoff(10) == 20
assert payoff(0) == 0
__tests_passed = 2
__tests_total = 2
"""
    ex_res = await client.post(
        f"/api/v1/learning/lessons/{lesson_id}/exercise",
        headers=inst_headers,
        json={
            "prompt_md": "Return double the payoff",
            "starter_code": "def payoff(x):\n    return x\n",
            "tests_code": tests_code,
            "language": "python",
        },
    )
    exercise_id = ex_res.json()["id"]

    # 2. Register student in the same tenant
    _, stud_token = await _create_student_in_tenant(
        db_session,
        tenant_id,
        email=f"charlie-{uuid.uuid4().hex[:6]}@princeton.edu",
    )
    stud_headers = {"Authorization": f"Bearer {stud_token}"}

    # 3. Attempt to submit before enrolling -> 403 Forbidden
    unauth_sub = await client.post(
        f"/api/v1/learning/exercises/{exercise_id}/submit",
        headers=stud_headers,
        json={"code": "def payoff(x): return x * 2"},
    )
    assert unauth_sub.status_code == 403

    # 4. Enroll student
    await client.post(f"/api/v1/learning/courses/{course_id}/enroll", headers=stud_headers)

    # 5. Submit correct code
    sub_res = await client.post(
        f"/api/v1/learning/exercises/{exercise_id}/submit",
        headers=stud_headers,
        json={"code": "def payoff(x):\n    return x * 2\n"},
    )
    assert sub_res.status_code == 200
    sub_id = sub_res.json()["submission_id"]
    assert sub_res.json()["status"] == "queued"

    # 6. Poll submission status until terminal state
    data = None
    for _ in range(20):
        await asyncio.sleep(0.15)
        status_res = await client.get(
            f"/api/v1/learning/submissions/{sub_id}",
            headers=stud_headers,
        )
        assert status_res.status_code == 200
        data = status_res.json()
        if data["status"] in ("passed", "failed", "error"):
            break

    assert data is not None
    assert data["status"] == "passed"
    assert data["tests_passed"] == 2
    assert data["tests_total"] == 2
