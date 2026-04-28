"""Validate .env files against a schema of required keys and optional rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class ValidationError:
    key: str
    message: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"ValidationError(key={self.key!r}, message={self.message!r})"


@dataclass
class ValidationResult:
    errors: List[ValidationError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def __repr__(self) -> str:  # pragma: no cover
        return f"ValidationResult(ok={self.ok}, errors={self.errors!r})"


def validate_env(
    env: Dict[str, str],
    required_keys: Optional[List[str]] = None,
    patterns: Optional[Dict[str, str]] = None,
    non_empty: Optional[List[str]] = None,
) -> ValidationResult:
    """Validate *env* dict against optional rules.

    Args:
        env: Parsed key/value mapping from a .env file.
        required_keys: Keys that must be present (value may be empty).
        patterns: Mapping of key -> regex pattern the value must fully match.
        non_empty: Keys whose values must not be empty strings.

    Returns:
        A :class:`ValidationResult` with any collected errors.
    """
    errors: List[ValidationError] = []

    for key in required_keys or []:
        if key not in env:
            errors.append(ValidationError(key=key, message="required key is missing"))

    for key in non_empty or []:
        if key in env and env[key] == "":
            errors.append(ValidationError(key=key, message="value must not be empty"))

    for key, pattern in (patterns or {}).items():
        if key in env:
            if not re.fullmatch(pattern, env[key]):
                errors.append(
                    ValidationError(
                        key=key,
                        message=f"value {env[key]!r} does not match pattern {pattern!r}",
                    )
                )

    return ValidationResult(errors=errors)
