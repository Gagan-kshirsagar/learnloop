# Decision Log
## 2026-… — Modular monolith with enforced boundaries
Decision: one deployable FastAPI app, modules with a public api.py, CI fails on
cross-module internal imports. Why: microservice-like isolation without the
distributed tax; extractable later. Rejected: microservices (premature).

## 2026-… — Performance budgets as CI gates
Decision: bundle-size + Lighthouse budgets in CI. Why: regressions fail the build,
not the user. Rejected: perf dashboards (ignored in practice).
