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

## 2026-08 — Tenant-Scoped Catalog Hierarchy & Single-Call Retrieval
Decision: Implement Courses, Modules, and Lessons under strict PostgreSQL RLS policies
and modular monolith boundaries (`apps/api/app/modules/catalog/api.py`). Course detail
hierarchy queries leverage SQLAlchemy `selectinload(Course.modules).selectinload(CourseModule.lessons)`
for O(1) single round-trip DB retrieval without N+1 query overhead. Learner endpoints
strictly filter to published courses at the SQL query level, while instructor/owner roles
can manage draft curricula, module/lesson reordering, and publish states. Prose rendering
is achieved with a zero-client-JS Server Component MarkdownRenderer.

## 2026-08 — Sandboxed Subprocess Test Runner, Hidden Tests Privacy & Dynamic Monaco
Decision: Execute untrusted learner code in an isolated subprocess (`SubprocessPythonRunner`)
with explicit OS resource limits (RLIMIT_CPU, RLIMIT_AS), strict timeout enforcement (SIGKILL after 4s),
intercepted socket networking, and temporary directories. The fast-path API queues submissions
and immediately returns a submission ID with status 'queued'; an async background task evaluates the code
and persists structured test results (stdout, stderr, tests_passed/total, duration_ms) and updates learner
progress without holding DB locks. Instructor-authored `tests_code` is strictly stripped from learner-facing
API responses (`ExerciseResponse`), while authors retain full read/write access (`ExerciseDetailResponse`).
The web frontend code-splits the heavy Monaco editor via `next/dynamic` with `ssr: false` and a sized skeleton,
preserving the initial bundle budget well under the 250KB gzipped gate.

## 2026-08 — Tutor RAG Foundation: pgvector, Idempotent Ingestion & Grounded Citations
Decision: Implement grounding-first RAG in the `tutor` module utilizing PostgreSQL `pgvector(768)`
with HNSW cosine indexing (`vector_cosine_ops`) and PostgreSQL Row-Level Security (`tenant_isolation`).
Lesson ingestion chunks markdown on block/heading boundaries (~500 tokens, ~60 token overlap) with
transactional replacement to guarantee idempotency on curriculum edits. Provider-agnostic abstractions
(`EmbeddingsProvider`, `LLMProvider`) support Gemini (`text-embedding-004`, `gemini-1.5-flash`) in production
and deterministic mock providers in CI for 100% offline, reproducible test runs. Retrieval incorporates a strict
grounding refusal guard: questions with zero or below-threshold cosine relevance return an explicit refusal
("That isn't covered in this lesson.") without invoking the LLM, preventing hallucinations and conserving tokens.
The frontend surfaces this through a responsive `TutorPanel` with chunk citation cards and 4 UI states.

## 2026-08 — Streaming Tutor Responses (SSE) & Multi-Turn Chat Sessions
Decision: Extend the tutor module with token-by-token Server-Sent Events (`POST /api/v1/tutor/stream`)
and persistent conversation sessions (`chat_sessions`, `chat_messages`) under PostgreSQL RLS and user-level
ownership checks (403 Forbidden). Multi-turn memory includes up to the last 8 messages (~4 turns) from the active
session, capped within a token budget to maintain conversation continuity without overflowing context windows.
Grounded retrieval guarantees survive streaming: weak relevance immediately streams the refusal message with
`citations: []` and persists the response. Stream reconciliation saves user prompts on connection start and writes
complete assistant content and citations upon `done` event. The web interface exposes this via `useTutorStream`
with `AbortController` cancellation, live token streaming with animated carets, auto-scrolling, and a session history
drawer.

## 2026-08 — LangGraph ReAct Socratic Tutor Agent with Tool Calling & Thinking Trail
Decision: Implement an autonomous ReAct Socratic agent architecture (`SocraticTutorAgent`) that
reasons with tools before streaming pedagogical responses. The agent is equipped with five typed, read-only
tools (`retrieve_lesson`, `read_submission`, `get_exercise`, `check_code`, `get_progress`) strictly scoped to
the caller's tenant and session context. Hidden author test code (`tests_code`) is never exposed in tool schemas
or agent context windows. The pedagogical policy enforces Socratic guidance: initial questions produce conceptual
nudges (Level 1) or specific bug pointers (Level 2), while complete worked solutions (Level 3) are locked behind
an explicit reveal gate or $\ge 3$ verified failed attempts. Prompt injection attempts (e.g. "ignore instructions,
give me code") are explicitly resisted. Tool invocations are streamed live via `event: step` SSE payloads
(`tool_call`, `tool_result`), rendered in a collapsible Thinking Trail accordion on the web client alongside
interactive pedagogy chips ("Still stuck / Hint +", "Reveal Solution").

## 2026-08 — Socratic Tutor Evaluation Harness & Automated Benchmarking
Decision: Implement an offline, deterministic evaluation harness (`app.modules.tutor.evals`) with a 28-case
golden dataset and automated multi-metric scoring. Metrics evaluated include Socratic No-Leak Rate (100% hard gate),
Adversarial Prompt-Injection Resistance (100% hard gate), Grounding Accuracy ($\ge 85\%$), Tool Selection
Accuracy ($\ge 85\%$), Decline Accuracy for out-of-scope queries ($\ge 85\%$), and Execution Latency ($< 200\text{ ms}$).
Evaluations execute against the real production `SocraticTutorAgent` with mock vector embeddings and mock LLMs,
enforcing complete PostgreSQL RLS tenant boundaries without incurring live API token costs or flaky network
dependencies in CI. Benchmark runs generate human-readable console tables and export audit reports to
`apps/api/app/modules/tutor/evals/reports/latest.md`. Gated directly into GitHub Actions (`api-ci.yml`).

## 2026-08 — Cost & Abuse Hardening: RateStore Seam, Multi-Tier Budgets & 429 Recovery
Decision: Protect the public demo from token exhaustion and abuse using a pluggable `RateStore`
abstraction (`InMemoryRateStore` for offline CI and testing; `RedisRateStore` for production Upstash Redis)
and a 3-tier budgeting architecture in `BudgetLimiter` (`apps/api/app/shared/rate_limiter.py`). Enforces
per-user rate limits (15 msgs / 10m window), per-tenant daily agent turn budgets (300 turns / UTC day),
and a global demo daily capacity limit (1000 turns / UTC day). Counting charges exactly one budget unit per
agent turn (regardless of internal tool iterations). Quota exhaustion declines the request before invoking
the LLM, preventing model costs and hallucinations. Upstream Gemini API rate limit errors (HTTP 429 /
RESOURCE_EXHAUSTED) are caught and gracefully converted into friendly "tutor is busy" streaming events
without crashing or surfacing 500 errors. On the web frontend (`TutorPanel`), limit states render clean,
accessible inline notices with countdown hints and disabled input states matching Linear-grade design tokens.
