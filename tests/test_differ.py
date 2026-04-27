"""Tests for envlens.differ."""

import pytest

from envlens.differ import DiffStatus, diff_envs


BASE = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET_KEY": "changeme"}
TARGET_COMPLETE = {"DB_HOST": "prod.db", "DB_PORT": "5432", "SECRET_KEY": "s3cr3t"}
TARGET_MISSING = {"DB_HOST": "prod.db", "DB_PORT": "5432"}
TARGET_EXTRA = {"DB_HOST": "prod.db", "DB_PORT": "5432", "SECRET_KEY": "s3cr3t", "NEW_VAR": "new"}


def test_no_issues_when_keys_match():
    result = diff_envs(BASE, TARGET_COMPLETE)
    assert not result.missing
    assert not result.extra
    assert not result.has_issues


def test_detects_missing_key():
    result = diff_envs(BASE, TARGET_MISSING)
    assert len(result.missing) == 1
    assert result.missing[0].key == "SECRET_KEY"
    assert result.missing[0].status == DiffStatus.MISSING
    assert result.has_issues


def test_detects_extra_key():
    result = diff_envs(BASE, TARGET_EXTRA)
    assert len(result.extra) == 1
    assert result.extra[0].key == "NEW_VAR"
    assert result.extra[0].status == DiffStatus.EXTRA


def test_detects_value_mismatch_when_enabled():
    result = diff_envs(BASE, TARGET_COMPLETE, check_values=True)
    mismatched_keys = {e.key for e in result.mismatched}
    assert "DB_HOST" in mismatched_keys
    assert "SECRET_KEY" in mismatched_keys
    assert "DB_PORT" not in mismatched_keys


def test_no_mismatch_when_check_values_disabled():
    result = diff_envs(BASE, TARGET_COMPLETE, check_values=False)
    assert not result.mismatched


def test_empty_envs_produce_no_issues():
    result = diff_envs({}, {})
    assert not result.has_issues
    assert result.entries == []


def test_base_empty_all_keys_are_extra():
    result = diff_envs({}, {"FOO": "bar", "BAZ": "qux"})
    assert len(result.extra) == 2
    assert not result.missing


def test_target_empty_all_keys_are_missing():
    result = diff_envs({"FOO": "bar", "BAZ": "qux"}, {})
    assert len(result.missing) == 2
    assert not result.extra


def test_result_labels():
    result = diff_envs(BASE, TARGET_COMPLETE, base_name=".env.example", target_name=".env")
    assert result.base_name == ".env.example"
    assert result.target_name == ".env"


def test_ok_entries_captured():
    result = diff_envs(BASE, TARGET_COMPLETE)
    ok_keys = {e.key for e in result.ok}
    assert "DB_PORT" in ok_keys
