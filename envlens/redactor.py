"""Redactor module: mask sensitive values in .env variable sets."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Keys whose values should always be redacted regardless of user rules
_DEFAULT_SENSITIVE_PATTERNS: List[str] = [
    r".*SECRET.*",
    r".*PASSWORD.*",
    r".*PASSWD.*",
    r".*TOKEN.*",
    r".*API_KEY.*",
    r".*PRIVATE_KEY.*",
    r".*CREDENTIALS.*",
]

REDACTED_PLACEHOLDER = "***REDACTED***"


@dataclass
class RedactResult:
    """Holds the redacted variable map and metadata."""

    original_count: int
    redacted_keys: List[str]
    variables: Dict[str, str]

    @property
    def redacted_count(self) -> int:
        return len(self.redacted_keys)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RedactResult(original_count={self.original_count}, "
            f"redacted_count={self.redacted_count})"
        )


def _is_sensitive(key: str, patterns: List[str]) -> bool:
    """Return True if *key* matches any of the compiled regex patterns."""
    upper = key.upper()
    return any(re.fullmatch(pat, upper) for pat in patterns)


def redact(
    variables: Dict[str, str],
    extra_patterns: Optional[List[str]] = None,
    placeholder: str = REDACTED_PLACEHOLDER,
) -> RedactResult:
    """Return a RedactResult with sensitive values replaced by *placeholder*.

    Args:
        variables: Mapping of env key -> value (e.g. from parse_env_file).
        extra_patterns: Additional regex patterns (matched against uppercased key).
        placeholder: String to substitute for sensitive values.
    """
    patterns = list(_DEFAULT_SENSITIVE_PATTERNS)
    if extra_patterns:
        patterns.extend(extra_patterns)

    redacted_keys: List[str] = []
    result: Dict[str, str] = {}

    for key, value in variables.items():
        if _is_sensitive(key, patterns):
            result[key] = placeholder
            redacted_keys.append(key)
        else:
            result[key] = value

    return RedactResult(
        original_count=len(variables),
        redacted_keys=sorted(redacted_keys),
        variables=result,
    )
