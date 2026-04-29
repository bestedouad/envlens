"""Lint .env files for common style and safety issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class LintSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass
class LintIssue:
    key: str
    message: str
    severity: LintSeverity

    def __repr__(self) -> str:  # pragma: no cover
        return f"LintIssue({self.severity.value}, {self.key!r}: {self.message})"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.severity == LintSeverity.ERROR for i in self.issues)

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == LintSeverity.WARNING]

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == LintSeverity.ERROR]


def lint_env(variables: Dict[str, str]) -> LintResult:
    """Run all lint rules against a parsed env mapping and return a LintResult."""
    result = LintResult()

    for key, value in variables.items():
        _check_key_format(key, result)
        _check_empty_value(key, value, result)
        _check_potential_secret_exposed(key, value, result)

    return result


# ── private rules ──────────────────────────────────────────────────────────────

_SECRET_KEYWORDS = ("password", "secret", "token", "apikey", "api_key", "private")
_PLACEHOLDER_VALUES = ("", "changeme", "todo", "fixme", "placeholder", "your_value_here")


def _check_key_format(key: str, result: LintResult) -> None:
    if not key.isupper():
        result.issues.append(
            LintIssue(
                key=key,
                message="Key should be UPPER_SNAKE_CASE",
                severity=LintSeverity.WARNING,
            )
        )
    if " " in key:
        result.issues.append(
            LintIssue(
                key=key,
                message="Key contains spaces",
                severity=LintSeverity.ERROR,
            )
        )


def _check_empty_value(key: str, value: str, result: LintResult) -> None:
    if value.strip() == "":
        result.issues.append(
            LintIssue(
                key=key,
                message="Value is empty",
                severity=LintSeverity.WARNING,
            )
        )


def _check_potential_secret_exposed(key: str, value: str, result: LintResult) -> None:
    lower_key = key.lower()
    if any(kw in lower_key for kw in _SECRET_KEYWORDS):
        if value.lower() in _PLACEHOLDER_VALUES:
            result.issues.append(
                LintIssue(
                    key=key,
                    message="Secret-like key has a placeholder or empty value",
                    severity=LintSeverity.WARNING,
                )
            )
