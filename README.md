# LearnLoop 🚀

**AI-Native, Multi-Tenant Learning Platform with Grounded Socratic Tutoring & Hardened Code Execution**

---

## 🌟 Overview
LearnLoop is an enterprise-grade learning platform built to senior software engineering standards. It delivers an AI-native educational experience with real-time interactive code sandboxing, deterministic curriculum embeddings, streaming Socratic tutoring, and verified multi-tenant PostgreSQL Row-Level Security (RLS).

---

## 🏗️ Architecture & Modular Monolith
LearnLoop uses an enforced modular monolith architecture where each domain exposes exactly one public interface (`api.py`):

```
apps/api/app/modules/
├── identity/       # Authentication, Tenant Management, Passwordless/JWT Auth
├── catalog/        # Course & Curriculum Management, Module/Lesson Hierarchies
├── learning/       # Enrollments, Code Execution Sandbox, Grading Pipeline
├── tutor/          # Grounded RAG, Socratic ReAct Agent, Evaluation Harness
│   ├── evals/      # 28-Case Golden Dataset, Automated Scorer, Benchmark Runner
│   └── internal/   # pgvector Embeddings, Gemini Router, LangGraph ReAct StateGraph
└── billing/        # Plan Quotas & Subscriptions
```

---

## 🤖 Socratic AI Tutor Agent & Evaluation Harness

The AI Tutor is an autonomous **LangGraph ReAct Agent** that uses progressive hint escalation to guide students to discover answers on their own without premature code dumps.

### Core Pedagogical Capabilities:
- **3-Tier Socratic Hinting:** Nudge (Level 1) $\to$ Specific Bug Pointer (Level 2) $\to$ Worked Solution (Level 3, gated behind explicit requests or $\ge 3$ failed attempts).
- **Read-Only Tool Access:** Inspects submissions, retrieves grounded lesson chunks via pgvector, and checks progress with zero hidden test code exposure.
- **Adversarial Prompt-Injection Defense:** Detects and blocks jailbreaks (`ignore previous instructions`, `system override`, `admin mode`).

### Automated Offline Evaluation Benchmark
The tutor includes an automated evaluation harness with a **28-case golden benchmark dataset**:

```bash
# Run deterministic evaluation benchmark locally or in CI
cd apps/api
uv run python -m app.modules.tutor.evals.run --offline --threshold 0.85
```

#### Latest Benchmark Results:
- **Overall Pass Rate:** **`100%`** (28/28 test cases passed, target $\ge 85\%$)
- **No-Leak Rate (Socratic):** **`100%`** (Zero premature solution leaks)
- **Prompt-Injection Resistance:** **`100%`** (100% refusal on adversarial bypass attempts)
- **Grounding Accuracy:** **`100%`**
- **Tool Selection Accuracy:** **`100%`**
- **Average Latency:** **`52.6 ms`** (Deterministic offline test suite)

👉 View the complete audit trail and methodology in [apps/api/app/modules/tutor/evals/reports/latest.md](file:///Users/gagankshirsagar/Desktop/learnloop/apps/api/app/modules/tutor/evals/reports/latest.md).

---

## 🧪 Testing & CI Gates

```bash
# Backend CI Suite (apps/api)
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run python tools/check_boundaries.py
uv run pytest
uv run python -m app.modules.tutor.evals.run --offline --threshold 0.85

# Frontend CI Suite (apps/web)
npm run lint
npm run typecheck
npm run test
npm run bundle-budget
```
