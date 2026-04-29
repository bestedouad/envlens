"""Tests for envlens.redactor."""

import pytest

from envlens.redactor import (
    REDACTED_PLACEHOLDER,
    RedactResult,
    redact,
    _is_sensitive,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _vars(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# _is_sensitive
# ---------------------------------------------------------------------------

def test_is_sensitive_matches_secret():
    from envlens.redactor import _DEFAULT_SENSITIVE_PATTERNS
    assert _is_sensitive("DB_SECRET", _DEFAULT_SENSITIVE_PATTERNS)


def test_is_sensitive_case_insensitive():
    from envlens.redactor import _DEFAULT_SENSITIVE_PATTERNS
    assert _is_sensitive("db_password", _DEFAULT_SENSITIVE_PATTERNS)


def test_is_sensitive_returns_false_for_plain_key():
    from envlens.redactor import _DEFAULT_SENSITIVE_PATTERNS
    assert not _is_sensitive("APP_ENV", _DEFAULT_SENSITIVE_PATTERNS)


# ---------------------------------------------------------------------------
# redact — basic behaviour
# ---------------------------------------------------------------------------

def test_redact_returns_redact_result():
    result = redact(_vars(APP_ENV="production"))
    assert isinstance(result, RedactResult)


def test_redact_preserves_non_sensitive_values():
    result = redact(_vars(APP_ENV="production", PORT="8080"))
    assert result.variables["APP_ENV"] == "production"
    assert result.variables["PORT"] == "8080"


def test_redact_masks_password():
    result = redact(_vars(DB_PASSWORD="s3cr3t"))
    assert result.variables["DB_PASSWORD"] == REDACTED_PLACEHOLDER


def test_redact_masks_token():
    result = redact(_vars(GITHUB_TOKEN="ghp_abc123"))
    assert result.variables["GITHUB_TOKEN"] == REDACTED_PLACEHOLDER


def test_redact_masks_api_key():
    result = redact(_vars(STRIPE_API_KEY="sk_live_xyz"))
    assert result.variables["STRIPE_API_KEY"] == REDACTED_PLACEHOLDER


def test_redact_records_redacted_keys():
    result = redact(_vars(DB_PASSWORD="x", APP_NAME="myapp", AUTH_TOKEN="t"))
    assert "DB_PASSWORD" in result.redacted_keys
    assert "AUTH_TOKEN" in result.redacted_keys
    assert "APP_NAME" not in result.redacted_keys


def test_redact_count_matches_redacted_keys():
    result = redact(_vars(DB_SECRET="s", APP_ENV="prod", API_KEY_INTERNAL="k"))
    assert result.redacted_count == len(result.redacted_keys)


def test_redact_original_count():
    variables = _vars(A="1", B="2", DB_PASSWORD="x")
    result = redact(variables)
    assert result.original_count == 3


# ---------------------------------------------------------------------------
# redact — extra patterns
# ---------------------------------------------------------------------------

def test_redact_extra_pattern_masks_matching_key():
    result = redact(_vars(INTERNAL_HASH="abc"), extra_patterns=[r".*HASH.*"])
    assert result.variables["INTERNAL_HASH"] == REDACTED_PLACEHOLDER


def test_redact_custom_placeholder():
    result = redact(_vars(DB_PASSWORD="secret"), placeholder="<hidden>")
    assert result.variables["DB_PASSWORD"] == "<hidden>"


# ---------------------------------------------------------------------------
# redact — empty input
# ---------------------------------------------------------------------------

def test_redact_empty_variables():
    result = redact({})
    assert result.original_count == 0
    assert result.redacted_count == 0
    assert result.variables == {}
