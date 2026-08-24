from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.shared.config import get_settings
from app.shared.rate_store import RateStore, get_rate_store


class LimitReason(StrEnum):
    USER_RATE_LIMIT = "user_rate_limit"
    TENANT_DAILY_BUDGET = "tenant_daily_budget"
    GLOBAL_DAILY_BUDGET = "global_daily_budget"


class LimitCheckResult(BaseModel):
    allowed: bool
    reason: LimitReason | None = None
    message: str = ""
    retry_after: int = 0
    current_count: int = 0
    limit: int = 0


class BudgetLimiter:
    """Manages multi-tier turn budgets and rate limits across users, tenants, and the demo."""

    def __init__(self, store: RateStore | None = None) -> None:
        self.store = store or get_rate_store()
        self.settings = get_settings()

    def _get_utc_date_str(self) -> str:
        return datetime.now(UTC).strftime("%Y%m%d")

    def _get_global_key(self, date_str: str) -> str:
        return f"learnloop:budget:global:{date_str}"

    def _get_tenant_key(self, tenant_id: UUID, date_str: str) -> str:
        return f"learnloop:budget:tenant:{tenant_id}:{date_str}"

    def _get_user_tutor_key(self, user_id: UUID) -> str:
        return f"learnloop:rate:user:{user_id}:tutor"

    async def check_tutor_turn(
        self,
        user_id: UUID,
        tenant_id: UUID,
    ) -> LimitCheckResult:
        """Check all 3 budget tiers before running agent turn.

        Enforces in order:
        1. Global daily budget (across all tenants)
        2. Per-tenant daily budget (for caller's organization)
        3. Per-user short-window rate limit (15 msgs / 10 min)
        """
        date_str = self._get_utc_date_str()
        day_window = 86400

        # 1. Global Daily Budget Check
        global_key = self._get_global_key(date_str)
        global_count = await self.store.get_count(global_key, window_seconds=day_window)
        if global_count >= self.settings.global_daily_budget_turns:
            return LimitCheckResult(
                allowed=False,
                reason=LimitReason.GLOBAL_DAILY_BUDGET,
                message=(
                    "The demo has reached its daily global capacity. "
                    "Please check back tomorrow."
                ),
                retry_after=day_window,
                current_count=global_count,
                limit=self.settings.global_daily_budget_turns,
            )

        # 2. Per-Tenant Daily Budget Check
        tenant_key = self._get_tenant_key(tenant_id, date_str)
        tenant_count = await self.store.get_count(tenant_key, window_seconds=day_window)
        if tenant_count >= self.settings.tenant_daily_budget_turns:
            return LimitCheckResult(
                allowed=False,
                reason=LimitReason.TENANT_DAILY_BUDGET,
                message=(
                    "The daily AI limit for your organization has been reached. "
                    "Please check back tomorrow."
                ),
                retry_after=day_window,
                current_count=tenant_count,
                limit=self.settings.tenant_daily_budget_turns,
            )

        # 3. Per-User Rate Limit Check (without consuming until turn execution)
        user_key = self._get_user_tutor_key(user_id)
        user_count = await self.store.get_count(
            user_key,
            window_seconds=self.settings.user_rate_limit_window_seconds,
        )
        if user_count >= self.settings.user_rate_limit_turns:
            return LimitCheckResult(
                allowed=False,
                reason=LimitReason.USER_RATE_LIMIT,
                message=(
                    "Slow down — you've reached the 10-minute message limit. "
                    "Please try again shortly."
                ),
                retry_after=max(1, self.settings.user_rate_limit_window_seconds // 10),
                current_count=user_count,
                limit=self.settings.user_rate_limit_turns,
            )

        return LimitCheckResult(allowed=True)

    async def consume_tutor_turn(
        self,
        user_id: UUID,
        tenant_id: UUID,
    ) -> None:
        """Atomically consume exactly 1 turn against user, tenant, and global budgets."""
        date_str = self._get_utc_date_str()
        day_window = 86400

        global_key = self._get_global_key(date_str)
        tenant_key = self._get_tenant_key(tenant_id, date_str)
        user_key = self._get_user_tutor_key(user_id)

        await self.store.increment_with_expiry(global_key, window_seconds=day_window, amount=1)
        await self.store.increment_with_expiry(tenant_key, window_seconds=day_window, amount=1)
        await self.store.increment_with_expiry(
            user_key,
            window_seconds=self.settings.user_rate_limit_window_seconds,
            amount=1,
        )

    async def check_and_consume_general(
        self,
        key: str,
        limit: int | None = None,
        window_seconds: int | None = None,
    ) -> tuple[bool, int]:
        """General rate limit check & consume for non-tutor compute endpoints."""
        lim = limit or self.settings.general_rate_limit_requests
        win = window_seconds or self.settings.general_rate_limit_window_seconds
        allowed, _, retry_after = await self.store.check_and_consume(
            key=f"learnloop:rate:general:{key}",
            limit=lim,
            window_seconds=win,
            amount=1,
        )
        return allowed, retry_after


_budget_limiter: BudgetLimiter | None = None


def get_budget_limiter() -> BudgetLimiter:
    global _budget_limiter
    if _budget_limiter is None:
        _budget_limiter = BudgetLimiter()
    return _budget_limiter
