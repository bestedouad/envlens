"""Scores a .env file for overall health based on lint, validation, and redaction signals."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envlens.linter import LintResult, LintSeverity
from envlens.validator import ValidationResult
from envlens.redactor import RedactResult


# Penalty weights
_LINT_ERROR_PENALTY = 10
_LINT_WARNING_PENALTY = 3
_VALIDATION_ERROR_PENALTY = 15
_UNREDACTED_SENSITIVE_PENALTY = 8

_MAX_SCORE = 100


@dataclass
class ScoreBreakdown:
    lint_penalty: int = 0
    validation_penalty: int = 0
    redaction_penalty: int = 0

    @property
    def total_penalty(self) -> int:
        return self.lint_penalty + self.validation_penalty + self.redaction_penalty


@dataclass
class ScoreResult:
    score: int
    grade: str
    breakdown: ScoreBreakdown
    notes: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return f"ScoreResult(score={self.score}, grade={self.grade!r})"


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def score_env(
    lint_result: LintResult | None = None,
    validation_result: ValidationResult | None = None,
    redact_result: RedactResult | None = None,
) -> ScoreResult:
    """Compute a health score (0-100) for a .env file from analysis results."""
    breakdown = ScoreBreakdown()
    notes: list[str] = []

    if lint_result is not None:
        errors = sum(1 for i in lint_result.issues if i.severity == LintSeverity.ERROR)
        warnings = sum(1 for i in lint_result.issues if i.severity == LintSeverity.WARNING)
        breakdown.lint_penalty = errors * _LINT_ERROR_PENALTY + warnings * _LINT_WARNING_PENALTY
        if errors:
            notes.append(f"{errors} lint error(s) found")
        if warnings:
            notes.append(f"{warnings} lint warning(s) found")

    if validation_result is not None:
        count = len(validation_result.errors)
        breakdown.validation_penalty = count * _VALIDATION_ERROR_PENALTY
        if count:
            notes.append(f"{count} validation error(s) found")

    if redact_result is not None:
        unredacted = sum(
            1 for v in redact_result.redacted.values() if v != "***REDACTED***"
        )
        breakdown.redaction_penalty = unredacted * _UNREDACTED_SENSITIVE_PENALTY
        if unredacted:
            notes.append(f"{unredacted} sensitive key(s) with exposed values")

    raw = _MAX_SCORE - breakdown.total_penalty
    score = max(0, min(_MAX_SCORE, raw))
    return ScoreResult(score=score, grade=_grade(score), breakdown=breakdown, notes=notes)
