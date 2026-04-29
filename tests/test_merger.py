"""Tests for envlens.merger."""
from __future__ import annotations

import pytest
from pathlib import Path

from envlens.merger import merge_env_files, MergeResult


@pytest.fixture()
def tmp_env(tmp_path: Path):
    """Return a helper that writes a .env file and gives back its path."""

    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content)
        return p

    return _write


def test_merge_single_file(tmp_env):
    p = tmp_env("base.env", "FOO=bar\nBAZ=qux\n")
    result = merge_env_files(p)
    assert result.merged == {"FOO": "bar", "BAZ": "qux"}


def test_later_file_overrides_earlier(tmp_env):
    base = tmp_env("base.env", "FOO=base\nSHARED=original\n")
    override = tmp_env("override.env", "SHARED=overridden\nEXTRA=yes\n")
    result = merge_env_files(base, override)
    assert result.merged["SHARED"] == "overridden"
    assert result.merged["FOO"] == "base"
    assert result.merged["EXTRA"] == "yes"


def test_overridden_keys_reports_conflicts(tmp_env):
    base = tmp_env("a.env", "KEY=one\n")
    override = tmp_env("b.env", "KEY=two\n")
    result = merge_env_files(base, override)
    assert "KEY" in result.overridden_keys


def test_no_overridden_keys_when_disjoint(tmp_env):
    a = tmp_env("a.env", "ALPHA=1\n")
    b = tmp_env("b.env", "BETA=2\n")
    result = merge_env_files(a, b)
    assert result.overridden_keys == []


def test_source_for_returns_last_writer(tmp_env):
    base = tmp_env("base.env", "KEY=from_base\n")
    top = tmp_env("top.env", "KEY=from_top\n")
    result = merge_env_files(base, top)
    assert result.source_for("KEY") == str(top)


def test_source_for_unknown_key_returns_none(tmp_env):
    p = tmp_env("only.env", "A=1\n")
    result = merge_env_files(p)
    assert result.source_for("MISSING") is None


def test_provenance_tracks_all_sources(tmp_env):
    a = tmp_env("a.env", "KEY=v1\n")
    b = tmp_env("b.env", "KEY=v2\n")
    c = tmp_env("c.env", "KEY=v3\n")
    result = merge_env_files(a, b, c)
    sources = [src for src, _ in result.provenance["KEY"]]
    assert sources == [str(a), str(b), str(c)]


def test_merge_returns_merge_result_instance(tmp_env):
    p = tmp_env("x.env", "X=1\n")
    result = merge_env_files(p)
    assert isinstance(result, MergeResult)


def test_empty_file_contributes_no_keys(tmp_env):
    empty = tmp_env("empty.env", "\n# just a comment\n")
    base = tmp_env("base.env", "REAL=value\n")
    result = merge_env_files(empty, base)
    assert result.merged == {"REAL": "value"}
