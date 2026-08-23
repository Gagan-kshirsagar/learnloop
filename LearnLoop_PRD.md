# LearnLoop — Product Requirements Document (PRD)

**Version:** 1.0 · **Status:** Draft for MVP · **Owner:** Gagan Kshirsagar

A concise, real-world PRD. It defines *what* we're building and *why*, so every
engineering slice traces back to a user need. (Being able to produce and reason
about a PRD is itself a senior/interview signal.)

---

## 1. Summary

LearnLoop is a multi-tenant, AI-native coding-education platform. Its core is an
**agentic AI tutor** that reads both the lesson and the learner's own code, then
guides them **Socratically** to their own fix — grounded in course content,
adapted to their mistakes, and transparent about its reasoning. It is sold to
organizations (bootcamps, universities, company L&D) that run isolated cohorts.

---

## 2. Problem statement

Learning to code breaks down at the moment of being stuck. Learners then either
(a) stall and lose momentum, or (b) copy a complete solution and learn nothing.
Existing options fail this moment:

- **Static courses** are one-size-fits-all — same video, same quiz, no one to ask.
- **Human tutoring** teaches well but doesn't scale and is expensive.
- **General AI (ChatGPT)** hands over full answers, ungrounded in the course, so
  it short-circuits learning and can be confidently wrong.

**The gap:** personalized, always-available help that teaches you to *think*,
grounded in your actual course, that refuses to just give the answer.

---

## 3. Goals & non-goals

### Goals (MVP)
- G1. A learner can get **unstuck via escalating Socratic hints** grounded in
  their lesson and their failing code — without being handed the solution.
- G2. **Practice that runs:** coding exercises with real, test-based pass/fail.
- G3. **Trust:** the tutor cites *why* (lesson section + code line); it declines
  when the answer isn't in the course rather than hallucinating.
- G4. **Multi-tenant SaaS foundation:** organizations, isolated data, roles.
- G5. **Measured quality:** evals prove the tutor stays Socratic (no-leak) and
  grounded — in CI, not by vibes.

### Non-goals (explicitly out, for now)
- N1. General-purpose chatbot / open-domain answers.
- N2. Subjects beyond coding (where safe execution + objective tests make the AI
  reliable). Math/others later.
- N3. Video hosting / marketing-site features. Content platform, tutor is the hero.
- N4. Enterprise compliance suite (SSO/SCIM/audit exports) — a later tier.
- N5. Human-graded open-ended essays / creative work.

---

## 4. Target users & personas

| Persona | Who | Core need |
|---|---|---|
| **Sam — the learner** (primary) | Self-learner / bootcamp student / early-career dev | In-the-moment help that doesn't spoil the learning; instant practice feedback |
| **Ira — the instructor** | Course creator / bootcamp teacher | Author courses once; have an AI tutor scale their teaching to every learner |
| **Tara — the tenant admin** | Bootcamp/university/L&D buyer | Run isolated cohorts; see who's progressing / at risk; manage seats & plan |

---

## 5. User stories (MVP)

**Learner (Sam)**
- As a learner, I can enroll in a course and work through lessons.
- As a learner, I can attempt a coding exercise in an editor and get instant
  pass/fail from real tests.
- As a learner, when stuck, I can ask the tutor and receive a **hint** grounded
  in my lesson and my code — escalating if I'm still stuck — **not** the full
  answer.
- As a learner, I can ask "why this hint?" and see the lesson section + the line
  of my code it refers to.
- As a learner, after a mistake I'm pointed to the **next step that fits my gap**.

**Instructor (Ira)**
- As an instructor, I can create a course with modules, lessons (markdown + code),
  and exercises (prompt + hidden tests).
- As an instructor, my lesson content grounds the tutor automatically.

**Tenant admin (Tara)**
- As an admin, I register my organization and invite instructors/learners.
- As an admin, my org's data is fully isolated from other orgs.
- As an admin, I can see cohort progress and which learners are at risk.
- As an admin, I'm on a plan (Free/Pro) with clear limits.

---

## 6. Functional requirements (MVP scope)

1. **Tenancy & auth** — org registration; users scoped to a tenant; roles
   (owner/instructor/student); pluggable auth (JWT now); demo-guest sandbox.
2. **Catalog** — courses → modules → lessons (markdown + code); asset storage.
3. **Learning** — enrollment; progress; exercises with a starter + hidden tests.
4. **Safe execution** — run learner code against tests in a hardened sandbox
   (timeout, no network, resource caps); return pass/fail + errors.
5. **Tutor (the hero)** — grounded RAG over lesson content; streaming chat;
   LangGraph agent with code-aware tools; **Socratic hint escalation** with a
   gated "reveal"; adaptive next-step; explainability ("why this hint").
6. **Async pipeline** — ingestion/grading/quiz-gen run as background jobs with
   status, never inline.
7. **Billing** — plans, per-tenant subscription, plan-gating (Stripe test).
8. **Evals & observability** — tutor no-leak + grounding evals in CI; tracing.

---

## 7. Non-functional requirements

- **Isolation:** cross-tenant data access is structurally impossible (Postgres
  RLS), proven by tests.
- **Scalability:** heavy AI work is async; modules have enforced boundaries so a
  service can be extracted without a rewrite.
- **Performance:** fast CRUD path < ~200ms; tutor first token streams quickly;
  long jobs are async with visible status.
- **Cost:** runnable on free tiers; model routing + caps keep unit economics and
  demo bills at ~$0.
- **Security/privacy:** minimal PII; learner data scoped and deletable; secrets
  in env; no private content used to train models.
- **Accessibility:** semantic, keyboard-operable, sufficient contrast.
- **Quality:** every feature tested; tutor quality measured by evals, not vibes.

---

## 8. The differentiators (why LearnLoop, not X)

1. **Code-aware Socratic tutor** — reads the learner's actual code + failing
   tests and guides, never dumps the answer. Most tools just answer.
2. **Grounded + explainable** — cites the lesson and the code line; declines when
   out of scope. No black box, no hallucinated advice.
3. **Evaluated pedagogy** — measures "did it stay Socratic / grounded" in CI. A
   genuinely novel eval axis.
4. **True SaaS foundation** — multi-tenant, async, billable — a scalable product,
   not a demo.

---

## 9. Success metrics

- **Learning:** stuck→solved **guided** (no answer given) in reduced time.
- **Pedagogy:** tutor no-leak rate and grounding rate (from evals) above target.
- **Engagement:** exercise completion; return usage; tutor turns/learner.
- **SaaS:** tenants onboarded; cohort progress; at-risk flags surfaced.
- **Ops:** ~$0 demo cost; async jobs succeed within SLA; zero cross-tenant leaks.

---

## 10. Release phases (maps to build slices)

- **Phase 0 — Foundation:** modular monolith + CI boundaries; multi-tenant auth.
- **Phase 1 — Content platform:** catalog + learning + Monaco editor + safe runner.
- **Phase 2 — The tutor:** async pipeline; RAG; streaming; LangGraph agent;
  Socratic escalation; adaptive next-step; model router.
- **Phase 3 — Startup & hardening:** billing; tutor evals; tracing; rate limits;
  deploy ($0); README.

Portfolio-worthy from the tutor slice on; a legitimately architected SaaS when
complete.

---

## 11. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Tutor leaks full solutions | Socratic prompt + reveal gate + **no-leak eval in CI** |
| Cross-tenant data leak | RLS at the DB + isolation test; never app-filter-only |
| Untrusted code execution | Hardened sandbox: timeout, no network, resource caps |
| AI cost blowup on public demo | Free key (rate-limits, never bills) + daily/per-IP caps + model router |
| Scope creep (becomes generic LMS) | Non-goals enforced; tutor stays the hero |
| Over-engineering the base | Modular monolith, NOT microservices; add complexity only on real signal |

---

## 12. Open questions (decide as we go)
- How strict is the "no full solution" gate, and when does "reveal" unlock?
- Teaching language(s) at MVP (Python-first for safe execution?).
- Depth of adaptivity (simple error-based next-step vs a concept graph).
- Analytics depth for tenant admins at MVP.
