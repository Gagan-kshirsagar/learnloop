import uuid

import pytest

from app.shared.config import Settings
from app.shared.rate_limiter import BudgetLimiter, LimitReason
from app.shared.rate_store import InMemoryRateStore


@pytest.mark.asyncio
async def test_in_memory_rate_store_basic_operations() -> None:
    store = InMemoryRateStore()
    key = "test:user:123"

    # Initial state
    assert await store.get_count(key, window_seconds=60) == 0

    # Increment
    count = await store.increment_with_expiry(key, window_seconds=60, amount=2)
    assert count == 2
    assert await store.get_count(key, window_seconds=60) == 2

    # Check and consume within limit
    allowed, count, retry_after = await store.check_and_consume(
        key=key, limit=5, window_seconds=60, amount=2
    )
    assert allowed is True
    assert count == 4
    assert retry_after == 0

    # Exceed limit
    allowed, count, retry_after = await store.check_and_consume(
        key=key, limit=5, window_seconds=60, amount=2
    )
    assert allowed is False
    assert count == 4
    assert retry_after > 0

    # Reset
    await store.reset(key)
    assert await store.get_count(key, window_seconds=60) == 0


@pytest.mark.asyncio
async def test_budget_limiter_tiers_and_isolation() -> None:
    store = InMemoryRateStore()
    limiter = BudgetLimiter(store=store)

    # Override limits for testing
    limiter.settings = Settings(
        user_rate_limit_turns=3,
        user_rate_limit_window_seconds=60,
        tenant_daily_budget_turns=5,
        global_daily_budget_turns=8,
    )

    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    user_a1 = uuid.uuid4()
    user_a2 = uuid.uuid4()

    # User A1 consumes 3 turns
    for _ in range(3):
        res = await limiter.check_tutor_turn(user_id=user_a1, tenant_id=tenant_a)
        assert res.allowed is True
        await limiter.consume_tutor_turn(user_id=user_a1, tenant_id=tenant_a)

    # User A1 hits user rate limit
    res_a1 = await limiter.check_tutor_turn(user_id=user_a1, tenant_id=tenant_a)
    assert res_a1.allowed is False
    assert res_a1.reason == LimitReason.USER_RATE_LIMIT

    # User A2 in Tenant A can still make requests (has not exceeded user rate limit)
    res_a2 = await limiter.check_tutor_turn(user_id=user_a2, tenant_id=tenant_a)
    assert res_a2.allowed is True

    # User A2 consumes 2 more turns -> total tenant turns = 5
    for _ in range(2):
        await limiter.consume_tutor_turn(user_id=user_a2, tenant_id=tenant_a)

    # Tenant A daily budget is now exhausted
    res_tenant_cap = await limiter.check_tutor_turn(user_id=user_a2, tenant_id=tenant_a)
    assert res_tenant_cap.allowed is False
    assert res_tenant_cap.reason == LimitReason.TENANT_DAILY_BUDGET

    # Tenant B is completely unaffected by Tenant A's budget exhaustion
    user_b1 = uuid.uuid4()
    res_b1 = await limiter.check_tutor_turn(user_id=user_b1, tenant_id=tenant_b)
    assert res_b1.allowed is True

    # Consume 3 turns for Tenant B -> total global = 5 + 3 = 8
    for _ in range(3):
        await limiter.consume_tutor_turn(user_id=user_b1, tenant_id=tenant_b)

    # Global demo daily budget is now exhausted (8 turns reached)
    user_c = uuid.uuid4()
    tenant_c = uuid.uuid4()
    res_global_cap = await limiter.check_tutor_turn(user_id=user_c, tenant_id=tenant_c)
    assert res_global_cap.allowed is False
    assert res_global_cap.reason == LimitReason.GLOBAL_DAILY_BUDGET
