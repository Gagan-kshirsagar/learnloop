# Decision Log
## 2026-… — Modular monolith with enforced boundaries
Decision: one deployable FastAPI app, modules with a public api.py, CI fails on
cross-module internal imports. Why: microservice-like isolation without the
distributed tax; extractable later. Rejected: microservices (premature).

## 2026-… — Performance budgets as CI gates
Decision: bundle-size + Lighthouse budgets in CI. Why: regressions fail the build,
not the user. Rejected: perf dashboards (ignored in practice).

## 2026-08 — Multi-Tenant PostgreSQL RLS & Pluggable Authentication
Decision: Enforce multi-tenant data isolation strictly via PostgreSQL Row-Level
Security policies (`tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid`)
with tenant-scoped sessions (`SET LOCAL app.tenant_id` / `set_config('app.tenant_id', ..., true)`).
A narrowly scoped `get_privileged_session` is used solely for initial registration
and pre-login email lookups. Pluggable AuthProvider seam abstracts JWT vs Firebase.
Access tokens (~30m lifetime) are kept in-memory client-side; refresh tokens (~7d)
are stored in local storage for fast client restore with seamless 401 retry interceptor
(with trade-off noted: client storage enables straightforward cross-origin dev and
instant session restore; production migration to httpOnly SameSite=Strict cookie
is transparent through the AuthProviderClient boundary).
