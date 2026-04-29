"""Integration tests for the snapshot CLI helpers."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


def _write(p: Path, content: str) -> Path:
    p.write_text(content)
    return p


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "envlens", *args],
        capture_output=True,
        text=True,
    )


@pytest.fixture()
def env_a(tmp_path) -> Path:
    return _write(tmp_path / ".env.a", "KEY=hello\nPORT=8000\n")


@pytest.fixture()
def env_b(tmp_path) -> Path:
    return _write(tmp_path / ".env.b", "KEY=world\nPORT=8000\nNEW=added\n")


# ── snapshot save ─────────────────────────────────────────────────────────────

def test_snapshot_save_exits_zero(env_a, tmp_path):
    out = tmp_path / "snap.json"
    result = _run("snapshot", "save", str(env_a), str(out))
    assert result.returncode == 0
    assert out.exists()


def test_snapshot_save_writes_valid_json(env_a, tmp_path):
    out = tmp_path / "snap.json"
    _run("snapshot", "save", str(env_a), str(out))
    data = json.loads(out.read_text())
    assert "variables" in data
    assert data["variables"]["KEY"] == "hello"


def test_snapshot_save_missing_env_exits_nonzero(tmp_path):
    out = tmp_path / "snap.json"
    result = _run("snapshot", "save", str(tmp_path / "missing.env"), str(out))
    assert result.returncode != 0


# ── snapshot diff ─────────────────────────────────────────────────────────────

def test_snapshot_diff_identical_exits_zero(env_a, tmp_path):
    snap1 = tmp_path / "s1.json"
    snap2 = tmp_path / "s2.json"
    _run("snapshot", "save", str(env_a), str(snap1))
    _run("snapshot", "save", str(env_a), str(snap2))
    result = _run("snapshot", "diff", str(snap1), str(snap2))
    assert result.returncode == 0
    assert "No changes" in result.stdout


def test_snapshot_diff_detects_changes(env_a, env_b, tmp_path):
    snap1 = tmp_path / "s1.json"
    snap2 = tmp_path / "s2.json"
    _run("snapshot", "save", str(env_a), str(snap1))
    _run("snapshot", "save", str(env_b), str(snap2))
    result = _run("snapshot", "diff", str(snap1), str(snap2))
    assert result.returncode == 1
    assert "+" in result.stdout or "~" in result.stdout


def test_snapshot_diff_json_format(env_a, env_b, tmp_path):
    snap1 = tmp_path / "s1.json"
    snap2 = tmp_path / "s2.json"
    _run("snapshot", "save", str(env_a), str(snap1))
    _run("snapshot", "save", str(env_b), str(snap2))
    result = _run("snapshot", "diff", str(snap1), str(snap2), "--format", "json")
    data = json.loads(result.stdout)
    assert "added" in data and "removed" in data and "changed" in data


def test_snapshot_diff_bad_snapshot_exits_nonzero(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    result = _run("snapshot", "diff", str(bad), str(bad))
    assert result.returncode != 0
