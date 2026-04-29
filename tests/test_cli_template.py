"""Integration tests for the *template* CLI subcommand."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


def _write(p: Path, content: str) -> Path:
    p.write_text(content, encoding="utf-8")
    return p


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "envlens", *args],
        capture_output=True,
        text=True,
    )


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    return _write(tmp_path / ".env", "SECRET=abc\nAPI_URL=https://example.com\n")


def test_template_exits_zero(env_file):
    result = _run("template", str(env_file))
    assert result.returncode == 0


def test_template_stdout_contains_keys(env_file):
    result = _run("template", str(env_file))
    assert "SECRET=" in result.stdout
    assert "API_URL=" in result.stdout


def test_template_stdout_strips_values(env_file):
    result = _run("template", str(env_file))
    assert "abc" not in result.stdout
    assert "https://example.com" not in result.stdout


def test_template_with_placeholder(env_file):
    result = _run("template", str(env_file), "--placeholder", "REQUIRED")
    assert "SECRET=REQUIRED" in result.stdout


def test_template_no_comments_flag(env_file):
    result = _run("template", str(env_file), "--no-comments")
    assert "# Generated" not in result.stdout


def test_template_with_output_file(env_file, tmp_path):
    out = tmp_path / ".env.example"
    result = _run("template", str(env_file), "-o", str(out))
    assert result.returncode == 0
    assert out.exists()
    assert "SECRET=" in out.read_text()


def test_template_missing_source_exits_two(tmp_path):
    result = _run("template", str(tmp_path / "nonexistent.env"))
    assert result.returncode == 2
    assert "not found" in result.stderr
