"""Tests for the audit module, which ties together parsing, diffing, and reporting."""

import pytest
from pathlib import Path

from envlens.audit import audit_files, audit_and_report, audit_many
from envlens.differ import DiffStatus


@pytest.fixture
def tmp_env(tmp_path):
    """Return a helper that writes a .env file and returns its path."""

    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content)
        return p

    return _write


# ---------------------------------------------------------------------------
# audit_files
# ---------------------------------------------------------------------------


def test_audit_files_returns_diff_result(tmp_env):
    base = tmp_env(".env.base", "KEY=value\nSHARED=same\n")
    target = tmp_env(".env.target", "KEY=value\nSHARED=same\n")

    result = audit_files(base, target)
    assert result.is_clean


def test_audit_files_detects_missing(tmp_env):
    base = tmp_env(".env.base", "KEY=value\nMISSING=x\n")
    target = tmp_env(".env.target", "KEY=value\n")

    result = audit_files(base, target)
    assert not result.is_clean
    statuses = {e.key: e.status for e in result.entries}
    assert statuses["MISSING"] == DiffStatus.MISSING


def test_audit_files_detects_extra(tmp_env):
    base = tmp_env(".env.base", "KEY=value\n")
    target = tmp_env(".env.target", "KEY=value\nEXTRA=bonus\n")

    result = audit_files(base, target)
    assert not result.is_clean
    statuses = {e.key: e.status for e in result.entries}
    assert statuses["EXTRA"] == DiffStatus.EXTRA


def test_audit_files_detects_value_mismatch(tmp_env):
    base = tmp_env(".env.base", "KEY=hello\n")
    target = tmp_env(".env.target", "KEY=world\n")

    result = audit_files(base, target, check_values=True)
    assert not result.is_clean
    statuses = {e.key: e.status for e in result.entries}
    assert statuses["KEY"] == DiffStatus.MISMATCH


def test_audit_files_no_mismatch_when_values_disabled(tmp_env):
    base = tmp_env(".env.base", "KEY=hello\n")
    target = tmp_env(".env.target", "KEY=world\n")

    result = audit_files(base, target, check_values=False)
    assert result.is_clean


# ---------------------------------------------------------------------------
# audit_and_report
# ---------------------------------------------------------------------------


def test_audit_and_report_returns_string(tmp_env):
    base = tmp_env(".env.base", "KEY=value\n")
    target = tmp_env(".env.target", "KEY=value\n")

    report = audit_and_report(base, target, use_color=False)
    assert isinstance(report, str)
    assert len(report) > 0


def test_audit_and_report_mentions_files(tmp_env):
    base = tmp_env(".env.base", "KEY=value\n")
    target = tmp_env(".env.target", "KEY=value\n")

    report = audit_and_report(base, target, use_color=False)
    assert ".env.base" in report or ".env.target" in report


# ---------------------------------------------------------------------------
# audit_many
# ---------------------------------------------------------------------------


def test_audit_many_all_clean(tmp_env):
    base = tmp_env(".env", "KEY=value\nOTHER=x\n")
    t1 = tmp_env(".env.staging", "KEY=value\nOTHER=x\n")
    t2 = tmp_env(".env.prod", "KEY=value\nOTHER=x\n")

    results = audit_many(base, [t1, t2])
    assert all(r.is_clean for r in results.values())


def test_audit_many_returns_keyed_by_path(tmp_env):
    base = tmp_env(".env", "KEY=value\n")
    t1 = tmp_env(".env.staging", "KEY=value\n")
    t2 = tmp_env(".env.prod", "KEY=value\n")

    results = audit_many(base, [t1, t2])
    assert t1 in results
    assert t2 in results


def test_audit_many_identifies_bad_target(tmp_env):
    base = tmp_env(".env", "KEY=value\nREQUIRED=yes\n")
    good = tmp_env(".env.staging", "KEY=value\nREQUIRED=yes\n")
    bad = tmp_env(".env.prod", "KEY=value\n")  # missing REQUIRED

    results = audit_many(base, [good, bad])
    assert results[good].is_clean
    assert not results[bad].is_clean
