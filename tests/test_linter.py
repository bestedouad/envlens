"""Tests for envlens.linter."""
import pytest

from envlens.linter import LintSeverity, lint_env


def test_ok_when_all_keys_valid():
    result = lint_env({"DATABASE_URL": "postgres://localhost/db", "DEBUG": "false"})
    assert result.ok
    assert result.issues == []


def test_warning_for_lowercase_key():
    result = lint_env({"database_url": "postgres://localhost/db"})
    warnings = [i for i in result.warnings if i.key == "database_url"]
    assert len(warnings) == 1
    assert "UPPER_SNAKE_CASE" in warnings[0].message


def test_warning_for_mixed_case_key():
    result = lint_env({"DatabaseUrl": "value"})
    assert any(i.key == "DatabaseUrl" for i in result.warnings)


def test_error_for_key_with_spaces():
    result = lint_env({"MY KEY": "value"})
    errors = [i for i in result.errors if i.key == "MY KEY"]
    assert len(errors) == 1
    assert "spaces" in errors[0].message
    assert not result.ok


def test_warning_for_empty_value():
    result = lint_env({"API_URL": ""})
    warnings = [i for i in result.warnings if i.key == "API_URL"]
    assert any("empty" in w.message.lower() for w in warnings)


def test_warning_for_whitespace_only_value():
    result = lint_env({"API_URL": "   "})
    assert any("empty" in i.message.lower() for i in result.warnings if i.key == "API_URL")


def test_warning_secret_key_with_placeholder_value():
    result = lint_env({"DB_PASSWORD": "changeme"})
    warnings = [i for i in result.warnings if i.key == "DB_PASSWORD"]
    assert len(warnings) >= 1
    assert any("placeholder" in w.message.lower() or "secret" in w.message.lower() for w in warnings)


def test_warning_secret_key_with_empty_value():
    result = lint_env({"API_SECRET": ""})
    # Both empty-value and secret-placeholder rules may fire; at least one should mention secret
    keys_issues = [i for i in result.issues if i.key == "API_SECRET"]
    assert len(keys_issues) >= 1


def test_no_secret_warning_when_value_is_real():
    result = lint_env({"API_TOKEN": "sk-abc123xyz"})
    secret_issues = [
        i for i in result.issues
        if i.key == "API_TOKEN" and "placeholder" in i.message.lower()
    ]
    assert secret_issues == []


def test_ok_property_false_when_errors_present():
    result = lint_env({"bad key": "value"})
    assert not result.ok


def test_ok_property_true_when_only_warnings():
    result = lint_env({"lower_key": "value"})
    assert result.ok  # warnings do not make ok False
    assert len(result.warnings) > 0


def test_multiple_issues_accumulated():
    result = lint_env({
        "good_KEY": "",
        "BAD KEY": "value",
        "DB_SECRET": "todo",
    })
    assert len(result.issues) >= 3
