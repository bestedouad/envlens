"""Tests for envlens.scorer."""

import pytest

from envlens.linter import LintResult, LintIssue, LintSeverity
from envlens.validator import ValidationResult, ValidationError
from envlens.redactor import RedactResult
from envlens.scorer import score_env, ScoreResult, _grade


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _lint(errors: int = 0, warnings: int = 0) -> LintResult:
    issues = []
    for _ in range(errors):
        issues.append(LintIssue(key="BAD_KEY", message="error", severity=LintSeverity.ERROR))
    for _ in range(warnings):
        issues.append(LintIssue(key="warn_key", message="warning", severity=LintSeverity.WARNING))
    return LintResult(issues=issues)


def _validation(errors: int = 0) -> ValidationResult:
    errs = [ValidationError(key=f"KEY_{i}", message="missing") for i in range(errors)]
    return ValidationResult(errors=errs)


def _redact(exposed: int = 0) -> RedactResult:
    redacted = {f"SECRET_{i}": "plaintext" for i in range(exposed)}
    return RedactResult(redacted=redacted, original_count=exposed)


# ---------------------------------------------------------------------------
# grade helper
# ---------------------------------------------------------------------------

def test_grade_a():
    assert _grade(100) == "A"
    assert _grade(90) == "A"


def test_grade_b():
    assert _grade(89) == "B"
    assert _grade(75) == "B"


def test_grade_c():
    assert _grade(74) == "C"
    assert _grade(60) == "C"


def test_grade_d():
    assert _grade(59) == "D"
    assert _grade(40) == "D"


def test_grade_f():
    assert _grade(39) == "F"
    assert _grade(0) == "F"


# ---------------------------------------------------------------------------
# score_env
# ---------------------------------------------------------------------------

def test_perfect_score_when_no_inputs():
    result = score_env()
    assert result.score == 100
    assert result.grade == "A"
    assert result.notes == []


def test_lint_errors_reduce_score():
    result = score_env(lint_result=_lint(errors=1))
    assert result.score == 90
    assert result.breakdown.lint_penalty == 10


def test_lint_warnings_reduce_score():
    result = score_env(lint_result=_lint(warnings=2))
    assert result.score == 94
    assert result.breakdown.lint_penalty == 6


def test_validation_errors_reduce_score():
    result = score_env(validation_result=_validation(errors=1))
    assert result.score == 85
    assert result.breakdown.validation_penalty == 15


def test_redaction_penalty_applied():
    result = score_env(redact_result=_redact(exposed=1))
    assert result.score == 92
    assert result.breakdown.redaction_penalty == 8


def test_combined_penalties():
    result = score_env(
        lint_result=_lint(errors=1, warnings=1),
        validation_result=_validation(errors=1),
        redact_result=_redact(exposed=1),
    )
    # 10 + 3 + 15 + 8 = 36 penalty
    assert result.score == 64
    assert result.grade == "C"


def test_score_clamped_to_zero():
    result = score_env(
        lint_result=_lint(errors=10),
        validation_result=_validation(errors=10),
    )
    assert result.score == 0


def test_notes_populated_for_issues():
    result = score_env(lint_result=_lint(errors=1, warnings=2))
    assert any("lint error" in n for n in result.notes)
    assert any("lint warning" in n for n in result.notes)


def test_score_result_repr_smoke():
    result = score_env()
    assert "ScoreResult" in repr(result)
