# AGENTS.md — Engineering Standards for LearnLoop


**Read fully before generating or modifying code. Follow strictly.** LearnLoop is
a multi-tenant, AI-native learning platform built to a senior standard, designed
to scale without a rewrite, and to feel fast and modern. Correctness, enforced
boundaries, performance, accessibility, tests, and clear reasoning matter more
than raw speed of delivery.

---

## 0. How to work here
- **Plan before coding.** Output a short plan (files, data flow, trade-offs) and
  wait for approval on non-trivial changes.
- **Thin vertical slices**, one feature at a time (UI → API → DB).
- **Every feature ships with tests.** Not done without them.
- **Never invent APIs.** Verify a library export exists before using it.
- **Record decisions** — new dependency or non-obvious choice → DECISIONS.md.
- **Small, conventional commits.**

## 1. Code style — write like an experienced human
- **Minimal comments.** Never narrate *what* a line does. Comment only non-obvious
  *why*, trade-offs, or warnings.
- **Names over comments.** Clear names + small functions remove the need for most
  comments. No commented-out code, no TODO litter.
- **Docstrings** = one-line purpose on public functions/services only.
- **Small units.** Prefer many small, well-named functions/components over long
  ones with section comments.

## 2. Architecture — modular monolith (ENFORCED boundaries)
```
apps/api/app/modules/{identity,catalog,learning,tutor,billing}/  (+ shared/)
```
- Each module exposes ONE public surface: `api.py`. Nothing outside a module may
  import its `internal/`. A **CI boundary check fails the build** on violation.
- `shared/` = cross-cutting infra (config, db, tenancy, events); keep it thin.
- **No microservices, no Kubernetes** until a real scaling/team signal.

## 3. Multi-tenancy (NON-NEGOTIABLE)
- `tenant_id` on every tenant-owned row. Isolation enforced by **Postgres RLS**,
  not app-layer `WHERE` alone. JWT carries `tenant_id`; a tenant-aware session
  sets the RLS context per request. No tenant query may bypass it.

## 4. AI-native async pipeline
- **Fast path (<200ms):** CRUD via sync FastAPI.
- **Slow path:** ingestion, grading, quiz-gen, heavy tutor reasoning → **queued**
  to a worker (Redis + Celery/Tasks); endpoints return a job id; UI shows status.
- Never do long AI work inline. Model access via a **model-router** abstraction
  (never hardcode one LLM). Untrusted learner code runs ONLY in the hardened
  sandbox (timeout, no network, resource caps) — never `exec()` in-process.

## 5. Backend rules
- FastAPI async; no blocking I/O in the loop. **Pydantic v2** for every request
  AND response (no bare dicts). **SQLAlchemy 2.0 async + Alembic** (migration per
  schema change; no raw SQL in routers). Per-module layering: `api.py` (thin) →
  service → repository. Config via env, prefixed `LEARNLOOP_`. No secrets in code.

## 6. Frontend rules — correctness
- Next.js App Router + **TypeScript strict**. No `any`; no non-null `!` without a
  reason.
- **Server state → TanStack Query ONLY.** **Client/UI state → Zustand ONLY.**
  Never fetch server data with `useState`/`useEffect`.
- HTTP via a single typed **Axios** instance (auth + tenant + error interceptors).
- **UI → shadcn/ui + Tailwind tokens only.** No second UI/styling library.
- Forms → react-hook-form + zod. Tables → TanStack Table.
- Every data view renders **loading / empty / error / success**. Long AI actions
  show **job status**, never a frozen UI.

## 7. Frontend rules — performance (see PERFORMANCE.md for the WHY)
- **Server Components by default;** add `"use client"` only at the leaf that needs
  interactivity. Push the client boundary as deep as possible.
- **Code-split** heavy/below-the-fold/rarely-used client components with
  `next/dynamic` (e.g. the Monaco editor, charts, the tutor panel).
- **Suspense + streaming** for async server data; skeletons sized to content.
- **Optimize images** (`next/image`, modern formats, explicit dimensions →
  protects CLS). **`next/font`** for fonts (no layout shift, no render-block).
- **Memoize deliberately** (`memo`/`useMemo`/`useCallback`) only where profiled or
  where a stable reference is needed; never reflexively.
- **Stable list keys** (id, never index). **Debounce/throttle** high-frequency
  handlers. **Virtualize** lists beyond a few hundred rows.
- **Prefetch** likely navigations; use TanStack Query `staleTime`/`placeholderData`
  to avoid refetch fl?ash. **Guard async** against stale responses + cancel on
  unmount.
- **Budget the bundle** — avoid heavy deps; import subpaths; check bundle in CI.

## 8. UI / UX standards (see UI_STANDARDS.md)
- Modern, spacious, confident (Linear/Vercel-grade). Design tokens only.
- **Purposeful motion** (Framer Motion): entrance fades/slides, layout
  transitions, press feedback, streaming/typing affordances — subtle, fast,
  **respecting `prefers-reduced-motion`**. No gratuitous animation.
- **Accessibility is required:** semantic elements, labels, keyboard, `aria-*`,
  visible focus, AA contrast. RTL-safe where feasible.

## 9. Quality bar
- Tests with every feature (RTL by role on FE; pytest happy + ≥1 failure on BE).
- Lint/format clean: ESLint (+jsx-a11y) + Prettier; Ruff + mypy. Plus the
  **module-boundary check** and **tenancy check**.
- CI green before merge: lint · typecheck · test · build · boundary · tenancy.
  Track a **Lighthouse/bundle budget** in CI where practical.
- Conventional Commits. Keep README/DECISIONS.md current.

## 10. Hard "do NOT" list
- ❌ Microservices/K8s/second DB prematurely · second UI library · `any`
- ❌ Server data in Zustand · `useEffect` fetching
- ❌ Tenant query without RLS scope · cross-module internal imports
- ❌ Long AI work inline · `exec()` learner code in-process · hardcoded LLM
- ❌ Business logic/raw SQL in routers · bare-dict responses · secrets in code
- ❌ Narrating comments · commented-out code · features without tests
- ❌ Index list keys · unoptimized images/fonts · client component where a server
  component would do

## 11. Definition of done (per feature)
- [ ] Matches the approved plan + this file. Tenant-scoped (RLS) if applicable.
- [ ] Respects module boundaries. Types complete (no `any`); FE mirrors BE schemas.
- [ ] Four UI states; long AI work queued with status.
- [ ] Performance: correct server/client split, code-split where heavy, images/
      fonts optimized, no obvious CLS/large bundle regression.
- [ ] Accessibility: keyboard + labels + roles + focus. Motion respects reduced-motion.
- [ ] Tests written + passing incl. a failure case. Lint/type/boundary/tenancy clean.
- [ ] Migration if schema changed; DECISIONS.md updated on a choice.
