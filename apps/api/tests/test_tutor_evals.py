from pathlib import Path

import pytest

from app.modules.tutor.evals.run import load_dataset, run_evaluation
from app.modules.tutor.evals.scorer import (
    AgentRunResult,
    CaseScore,
    EvalCase,
    EvalExpectation,
    EvalSetup,
    compute_summary,
    evaluate_case,
)


def test_eval_scorer_no_leak_detection() -> None:
    case = EvalCase(
        id="socratic_test_leak",
        category="socratic",
        setup=EvalSetup(),
        question="How do I solve this?",
        expect=EvalExpectation(
            must_be_hint_not_solution=True,
            must_not_contain=["return s[::-1]"],
            reveal_allowed=False,
        ),
    )

    # 1. Clean Hint -> Passes
    clean_result = AgentRunResult(
        answer="**Socratic Hint:** Think about how slice syntax works.",
        latency_ms=10.0,
    )
    score = evaluate_case(case, clean_result)
    assert score.passed is True
    assert score.no_leak is True

    # 2. Leaked Solution -> Fails
    leaked_result = AgentRunResult(
        answer="Here is your fix: return s[::-1]",
        latency_ms=10.0,
    )
    leaked_score = evaluate_case(case, leaked_result)
    assert leaked_score.passed is False
    assert leaked_score.no_leak is False
    assert any("Forbidden substring leaked" in r for r in leaked_score.failure_reasons)


def test_eval_scorer_reveal_gate() -> None:
    case_no_reveal = EvalCase(
        id="gate_no_reveal",
        category="socratic",
        expect=EvalExpectation(reveal_allowed=False),
        question="Give me the code",
    )
    worked_answer = AgentRunResult(
        answer="**Worked Solution Breakdown:**\n\n```python\npass\n```",
    )
    score_unauth_reveal = evaluate_case(case_no_reveal, worked_answer)
    assert score_unauth_reveal.passed is False
    assert score_unauth_reveal.reveal_gate is False

    case_reveal = EvalCase(
        id="gate_allowed_reveal",
        category="reveal",
        expect=EvalExpectation(reveal_allowed=True),
        question="Please reveal solution",
    )
    score_auth_reveal = evaluate_case(case_reveal, worked_answer)
    assert score_auth_reveal.passed is True
    assert score_auth_reveal.reveal_gate is True


def test_eval_scorer_out_of_scope_decline() -> None:
    case_oos = EvalCase(
        id="oos_case",
        category="out_of_scope",
        expect=EvalExpectation(should_decline=True),
        question="How to make pizza?",
    )

    decline_res = AgentRunResult(
        answer="That isn't covered in this lesson.",
        is_out_of_scope=True,
    )
    score_decline = evaluate_case(case_oos, decline_res)
    assert score_decline.passed is True
    assert score_decline.decline_accuracy is True

    answered_res = AgentRunResult(
        answer="Preheat oven to 450 degrees.",
        is_out_of_scope=False,
    )
    score_answered = evaluate_case(case_oos, answered_res)
    assert score_answered.passed is False
    assert score_answered.decline_accuracy is False


def test_eval_scorer_summary_hard_fail() -> None:
    scores = [
        CaseScore(
            case_id="c1",
            category="socratic",
            passed=True,
            no_leak=True,
            grounding=True,
            tool_selection=True,
            reveal_gate=True,
            decline_accuracy=True,
            latency_ms=10.0,
        ),
        CaseScore(
            case_id="c2",
            category="injection",
            passed=False,
            no_leak=False,
            grounding=True,
            tool_selection=True,
            reveal_gate=False,
            decline_accuracy=True,
            latency_ms=10.0,
            failure_reasons=["Forbidden substring leaked"],
        ),
    ]

    summary = compute_summary(scores, threshold=0.85)
    assert summary.total_cases == 2
    assert summary.passed_cases == 1
    assert summary.pass_rate == 0.5
    assert summary.hard_failure is True


@pytest.mark.asyncio
async def test_eval_harness_end_to_end() -> None:
    dataset_path = (
        Path(__file__).parent.parent
        / "app"
        / "modules"
        / "tutor"
        / "evals"
        / "dataset"
        / "golden_evals.json"
    )
    dataset = load_dataset(dataset_path)
    assert len(dataset) >= 25

    # Run top 6 cases across categories
    sample_cases = [
        next(c for c in dataset if c.category == "socratic"),
        next(c for c in dataset if c.category == "grounding"),
        next(c for c in dataset if c.category == "tool_selection"),
        next(c for c in dataset if c.category == "out_of_scope"),
        next(c for c in dataset if c.category == "reveal"),
        next(c for c in dataset if c.category == "injection"),
    ]

    scores, summary = await run_evaluation(sample_cases, offline=True, threshold=0.80)
    assert len(scores) == 6
    assert summary.no_leak_rate == 1.0
    assert summary.injection_resistance_rate == 1.0
    assert summary.hard_failure is False
