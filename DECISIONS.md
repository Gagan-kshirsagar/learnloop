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

