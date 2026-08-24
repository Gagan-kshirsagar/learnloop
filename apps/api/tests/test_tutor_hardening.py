import json
import uuid
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.modules.tutor.internal.llm import MockLLM
from app.modules.tutor.internal.router import get_model_router
from app.shared.rate_limiter import get_budget_limiter
from app.shared.rate_store import get_rate_store


async def _create_user(
    client: AsyncClient,
    email: str,
    org_name: str = "Test Org",
    name: str = "Test User",
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
async def test_tutor_stream_user_rate_limit(client: AsyncClient) -> None:
    store = get_rate_store()
    await store.reset()

    limiter = get_budget_limiter()
    original_turns = limiter.settings.user_rate_limit_turns
    limiter.settings.user_rate_limit_turns = 2

    try:
        user_id, tenant_id, token = await _create_user(
            client,
            f"user-{uuid.uuid4().hex[:6]}@demo.io",
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Turn 1
        res1 = await client.post(
            "/api/v1/tutor/stream",
            headers=headers,
            json={"question": "What is a variable?"},
        )
        assert res1.status_code == 200
        events1 = _parse_sse_events(res1.text)
        assert any(e["event"] == "done" for e in events1)

        # Turn 2
        res2 = await client.post(
            "/api/v1/tutor/stream",
            headers=headers,
            json={"question": "What is a function?"},
        )
        assert res2.status_code == 200
        events2 = _parse_sse_events(res2.text)
        assert any(e["event"] == "done" for e in events2)

        # Turn 3 -> Trips user rate limit
        res3 = await client.post(
            "/api/v1/tutor/stream",
            headers=headers,
            json={"question": "What is recursion?"},
        )
        assert res3.status_code == 200
        events3 = _parse_sse_events(res3.text)
        event_names3 = [e["event"] for e in events3]

        assert "limit" in event_names3
        limit_ev = next(e for e in events3 if e["event"] == "limit")
        limit_payload = json.loads(limit_ev["data"])
        assert limit_payload["reason"] == "user_rate_limit"
        assert "Slow down" in limit_payload["message"]

        # Tokens stream the polite decline
        tokens = [json.loads(e["data"])["text"] for e in events3 if e["event"] == "token"]
        assert "Slow down" in "".join(tokens)
        assert "done" in event_names3

    finally:
        limiter.settings.user_rate_limit_turns = original_turns
        await store.reset()


@pytest.mark.asyncio
async def test_tutor_stream_tenant_daily_budget_and_llm_bypass(client: AsyncClient) -> None:
    store = get_rate_store()
    await store.reset()

    limiter = get_budget_limiter()
    original_budget = limiter.settings.tenant_daily_budget_turns
    limiter.settings.tenant_daily_budget_turns = 1

    try:
        # Create Tenant A and Tenant B
        user_a, tenant_a, token_a = await _create_user(
            client,
            f"a-{uuid.uuid4().hex[:6]}@org-a.com",
            org_name="Org A",
        )
        user_b, tenant_b, token_b = await _create_user(
            client,
            f"b-{uuid.uuid4().hex[:6]}@org-b.com",
            org_name="Org B",
        )

        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # Tenant A: Turn 1 consumes the 1-turn budget
        res_a1 = await client.post(
            "/api/v1/tutor/stream",
            headers=headers_a,
            json={"question": "Explain arrays"},
        )
        assert res_a1.status_code == 200

        # Reset mock LLM call count to strictly verify bypass on turn 2
        model_router = get_model_router()
        mock_llm = model_router.get_llm_provider()
        if isinstance(mock_llm, MockLLM):
            mock_llm.call_count = 0

        # Tenant A: Turn 2 -> hits tenant daily cap
        res_a2 = await client.post(
            "/api/v1/tutor/stream",
            headers=headers_a,
            json={"question": "Explain linked lists"},
        )
        assert res_a2.status_code == 200
        events_a2 = _parse_sse_events(res_a2.text)

        limit_ev = next(e for e in events_a2 if e["event"] == "limit")
        limit_data = json.loads(limit_ev["data"])
        assert limit_data["reason"] == "tenant_daily_budget"
        assert "daily AI limit for your organization has been reached" in limit_data["message"]

        # ASSERT: Mock LLM was NOT called on capped turn
        if isinstance(mock_llm, MockLLM):
            assert mock_llm.call_count == 0

        # Tenant B is completely unaffected and works
        res_b = await client.post(
            "/api/v1/tutor/stream",
            headers=headers_b,
            json={"question": "Explain stacks"},
        )
        assert res_b.status_code == 200
        events_b = _parse_sse_events(res_b.text)
        assert not any(e["event"] == "limit" for e in events_b)
        assert any(e["event"] == "done" for e in events_b)

    finally:
        limiter.settings.tenant_daily_budget_turns = original_budget
        await store.reset()


@pytest.mark.asyncio
async def test_tutor_stream_global_daily_budget(client: AsyncClient) -> None:
    store = get_rate_store()
    await store.reset()

    limiter = get_budget_limiter()
    original_global = limiter.settings.global_daily_budget_turns
    limiter.settings.global_daily_budget_turns = 1

    try:
        user_1, tenant_1, token_1 = await _create_user(client, f"u1-{uuid.uuid4().hex[:6]}@demo.io")
        user_2, tenant_2, token_2 = await _create_user(client, f"u2-{uuid.uuid4().hex[:6]}@demo.io")

        # Turn 1 consumes global budget
        await client.post(
            "/api/v1/tutor/stream",
            headers={"Authorization": f"Bearer {token_1}"},
            json={"question": "Hello"},
        )

        model_router = get_model_router()
        mock_llm = model_router.get_llm_provider()
        if isinstance(mock_llm, MockLLM):
            mock_llm.call_count = 0

        # Turn 2 across any tenant hits global cap
        res2 = await client.post(
            "/api/v1/tutor/stream",
            headers={"Authorization": f"Bearer {token_2}"},
            json={"question": "Hello again"},
        )
        events2 = _parse_sse_events(res2.text)
        limit_ev = next(e for e in events2 if e["event"] == "limit")
        limit_data = json.loads(limit_ev["data"])
        assert limit_data["reason"] == "global_daily_budget"
        assert "daily global capacity" in limit_data["message"]

        if isinstance(mock_llm, MockLLM):
            assert mock_llm.call_count == 0

    finally:
        limiter.settings.global_daily_budget_turns = original_global
        await store.reset()


@pytest.mark.asyncio
async def test_tutor_stream_gemini_429_recovery(client: AsyncClient) -> None:
    store = get_rate_store()
    await store.reset()

    _, _, token = await _create_user(client, f"gemini429-{uuid.uuid4().hex[:6]}@demo.io")
    headers = {"Authorization": f"Bearer {token}"}

    model_router = get_model_router()
    mock_llm = model_router.get_llm_provider()
    if isinstance(mock_llm, MockLLM):
        mock_llm.simulate_429 = True

    try:
        res = await client.post(
            "/api/v1/tutor/stream",
            headers=headers,
            json={
                "question": "Why is my code failing with a bug?",
                "exercise_id": str(uuid.uuid4()),
            },
        )
        assert res.status_code == 200
        events = _parse_sse_events(res.text)

        limit_ev = next((e for e in events if e["event"] == "limit"), None)
        assert limit_ev is not None
        payload = json.loads(limit_ev["data"])
        assert payload["reason"] == "provider_busy"
        assert "busy handling high demand" in payload["message"]

        # Response must end cleanly with a done event (never crash or freeze)
        assert any(e["event"] == "done" for e in events)

    finally:
        if isinstance(mock_llm, MockLLM):
            mock_llm.simulate_429 = False
        await store.reset()


@pytest.mark.asyncio
async def test_single_agent_turn_consumes_exact_one_unit(client: AsyncClient) -> None:
    store = get_rate_store()
    await store.reset()

    user_id, tenant_id, token = await _create_user(client, f"units-{uuid.uuid4().hex[:6]}@demo.io")
    headers = {"Authorization": f"Bearer {token}"}

    # Stream an agent turn that uses tools
    res = await client.post(
        "/api/v1/tutor/stream",
        headers=headers,
        json={"question": "Why is my code failing with a syntax error?"},
    )
    assert res.status_code == 200

    limiter = get_budget_limiter()
    date_str = limiter._get_utc_date_str()
    tenant_count = await store.get_count(limiter._get_tenant_key(tenant_id, date_str))
    user_count = await store.get_count(limiter._get_user_tutor_key(user_id), window_seconds=600)
    global_count = await store.get_count(limiter._get_global_key(date_str))

    # Exactly 1 unit consumed despite tool steps
    assert tenant_count == 1
    assert user_count == 1
    assert global_count == 1

    await store.reset()


@pytest.mark.asyncio
async def test_learning_submit_rate_limit() -> None:
    store = get_rate_store()
    await store.reset()

    # Artificially fill rate limit for submit endpoint
    limiter = get_budget_limiter()
    for _ in range(30):
        await limiter.check_and_consume_general(
            key=f"submit:{_}",
            limit=30,
            window_seconds=60,
        )

    # Calling with current user after hitting 30 limit for that user
    user_key = "test_user_key"
    for _ in range(30):
        await store.increment_with_expiry(
            f"learnloop:rate:general:submit:{user_key}",
            window_seconds=60,
            amount=1,
        )

    allowed, retry_after = await limiter.check_and_consume_general(
        key=f"submit:{user_key}",
        limit=30,
        window_seconds=60,
    )
    assert allowed is False
    assert retry_after > 0
    await store.reset()
