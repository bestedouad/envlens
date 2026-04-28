"""Tests for the envlens CLI, including the new --export flag."""

from __future__ import annotations

import json
import os
import pathlib

import pytest

from envlens.cli import build_parser, main


@pytest.fixture()
def tmp_env(tmp_path: pathlib.Path):
    """Return a helper that writes a .env file and returns its path."""

    def _write(filename: str, content: str) -> str:
        p = tmp_path / filename
        p.write_text(content)
        return str(p)

    return _write


def _run(argv, capsys, expect_exit=0):
    with pytest.raises(SystemExit) as exc:
        main(argv)
    assert exc.value.code == expect_exit
    return capsys.readouterr()


# ── basic diff ────────────────────────────────────────────────────────────────

def test_diff_no_issues_exits_zero(tmp_env, capsys):
    ref = tmp_env(".env.example", "KEY=value\n")
    tgt = tmp_env(".env", "KEY=value\n")
    out = _run(["diff", ref, tgt], capsys, expect_exit=0)
    assert "No issues" in out.out or "KEY" in out.out or out.out  # report printed


def test_diff_missing_key_exits_one(tmp_env, capsys):
    ref = tmp_env(".env.example", "KEY=value\nSECRET=x\n")
    tgt = tmp_env(".env", "KEY=value\n")
    _run(["diff", ref, tgt], capsys, expect_exit=1)


def test_diff_extra_key_exits_one(tmp_env, capsys):
    ref = tmp_env(".env.example", "KEY=value\n")
    tgt = tmp_env(".env", "KEY=value\nEXTRA=oops\n")
    _run(["diff", ref, tgt], capsys, expect_exit=1)


# ── --export flag ─────────────────────────────────────────────────────────────

def test_diff_export_json(tmp_env, capsys):
    ref = tmp_env(".env.example", "KEY=a\nMISSING=b\n")
    tgt = tmp_env(".env", "KEY=a\n")
    out = _run(["diff", ref, tgt, "--export", "json"], capsys, expect_exit=1)
    data = json.loads(out.out)
    assert data["has_issues"] is True
    keys = [e["key"] for e in data["entries"]]
    assert "MISSING" in keys


def test_diff_export_csv(tmp_env, capsys):
    ref = tmp_env(".env.example", "KEY=a\n")
    tgt = tmp_env(".env", "KEY=a\n")
    out = _run(["diff", ref, tgt, "--export", "csv"], capsys, expect_exit=0)
    assert "key,status" in out.out


def test_diff_export_markdown(tmp_env, capsys):
    ref = tmp_env(".env.example", "KEY=a\n")
    tgt = tmp_env(".env", "KEY=a\n")
    out = _run(["diff", ref, tgt, "--export", "markdown"], capsys, expect_exit=0)
    assert "## envlens diff" in out.out
    assert "✅ No issues found." in out.out


# ── audit sub-command ─────────────────────────────────────────────────────────

def test_audit_multiple_targets_exits_one_on_any_issue(tmp_env, capsys):
    ref = tmp_env(".env.example", "A=1\nB=2\n")
    ok = tmp_env(".env.staging", "A=1\nB=2\n")
    bad = tmp_env(".env.prod", "A=1\n")
    _run(["audit", ref, ok, bad], capsys, expect_exit=1)


def test_audit_all_ok_exits_zero(tmp_env, capsys):
    ref = tmp_env(".env.example", "A=1\n")
    ok1 = tmp_env(".env.staging", "A=1\n")
    ok2 = tmp_env(".env.prod", "A=1\n")
    _run(["audit", ref, ok1, ok2], capsys, expect_exit=0)


def test_audit_export_json_multiple(tmp_env, capsys):
    ref = tmp_env(".env.example", "A=1\n")
    tgt = tmp_env(".env", "A=1\n")
    out = _run(["audit", ref, tgt, "--export", "json"], capsys, expect_exit=0)
    # Two JSON objects would be printed; check at least one is parseable
    data = json.loads(out.out.strip())
    assert "entries" in data
