"""Tests for envlens.validator."""

import pytest
from envlens.validator import validate_env, ValidationError, ValidationResult


def test_ok_when_no_rules():
    result = validate_env({"FOO": "bar", "BAZ": "1"})
    assert result.ok
    assert result.errors == []


def test_ok_when_all_required_keys_present():
    result = validate_env(
        {"DB_HOST": "localhost", "DB_PORT": "5432"},
        required_keys=["DB_HOST", "DB_PORT"],
    )
    assert result.ok


def test_error_when_required_key_missing():
    result = validate_env({"DB_HOST": "localhost"}, required_keys=["DB_HOST", "DB_PORT"])
    assert not result.ok
    assert len(result.errors) == 1
    assert result.errors[0].key == "DB_PORT"
    assert "missing" in result.errors[0].message


def test_error_when_multiple_required_keys_missing():
    result = validate_env({}, required_keys=["A", "B", "C"])
    assert len(result.errors) == 3
    missing_keys = {e.key for e in result.errors}
    assert missing_keys == {"A", "B", "C"}


def test_non_empty_passes_when_value_set():
    result = validate_env({"SECRET": "abc123"}, non_empty=["SECRET"])
    assert result.ok


def test_non_empty_fails_when_value_is_empty_string():
    result = validate_env({"SECRET": ""}, non_empty=["SECRET"])
    assert not result.ok
    assert result.errors[0].key == "SECRET"
    assert "empty" in result.errors[0].message


def test_non_empty_skips_missing_key():
    # If the key is absent entirely, non_empty rule should not fire
    # (required_keys handles presence; non_empty handles content)
    result = validate_env({}, non_empty=["SECRET"])
    assert result.ok


def test_pattern_passes_when_value_matches():
    result = validate_env(
        {"PORT": "8080"},
        patterns={"PORT": r"\d+"},
    )
    assert result.ok


def test_pattern_fails_when_value_does_not_match():
    result = validate_env(
        {"PORT": "not-a-number"},
        patterns={"PORT": r"\d+"},
    )
    assert not result.ok
    assert result.errors[0].key == "PORT"
    assert "does not match pattern" in result.errors[0].message


def test_pattern_skips_missing_key():
    result = validate_env({}, patterns={"PORT": r"\d+"})
    assert result.ok


def test_combined_rules_accumulate_all_errors():
    env = {"PORT": "abc", "EMPTY_VAL": ""}
    result = validate_env(
        env,
        required_keys=["MISSING_KEY"],
        non_empty=["EMPTY_VAL"],
        patterns={"PORT": r"\d+"},
    )
    assert not result.ok
    keys_with_errors = {e.key for e in result.errors}
    assert keys_with_errors == {"MISSING_KEY", "EMPTY_VAL", "PORT"}
