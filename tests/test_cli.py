"""Tests for the envlens CLI entry-point."""

import textwrap
import pytest

from envlens.cli import main


@pytest.fixture()
def tmp_env(tmp_path):
    """Return a helper that writes a .env file and returns its path."""

    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(textwrap.dedent(content))
        return str(p)

    return _write


# ---------------------------------------------------------------------------
# diff command
# ---------------------------------------------------------------------------

def test_diff_no_issues_exits_zero(tmp_env):
    ref = tmp_env(".env.example", "FOO=bar\nBAZ=qux\n")
    tgt = tmp_env(".env", "FOO=bar\nBAZ=qux\n")
    assert main(["diff", ref, tgt, "--no-color"]) == 0


def test_diff_missing_key_exits_one(tmp_env):
    ref = tmp_env(".env.example", "FOO=bar\nMISSING=x\n")
    tgt = tmp_env(".env", "FOO=bar\n")
    assert main(["diff", ref, tgt, "--no-color"]) == 1


def test_diff_extra_key_exits_one(tmp_env):
    ref = tmp_env(".env.example", "FOO=bar\n")
    tgt = tmp_env(".env", "FOO=bar\nEXTRA=oops\n")
    assert main(["diff", ref, tgt, "--no-color"]) == 1


def test_diff_value_mismatch_with_flag_exits_one(tmp_env):
    ref = tmp_env(".env.example", "FOO=bar\n")
    tgt = tmp_env(".env", "FOO=different\n")
    assert main(["diff", ref, tgt, "--check-values", "--no-color"]) == 1


def test_diff_value_mismatch_without_flag_exits_zero(tmp_env):
    ref = tmp_env(".env.example", "FOO=bar\n")
    tgt = tmp_env(".env", "FOO=different\n")
    assert main(["diff", ref, tgt, "--no-color"]) == 0


def test_diff_output_contains_filename(tmp_env, capsys):
    ref = tmp_env(".env.example", "FOO=bar\n")
    tgt = tmp_env(".env", "FOO=bar\n")
    main(["diff", ref, tgt, "--no-color"])
    captured = capsys.readouterr()
    assert ".env" in captured.out


# ---------------------------------------------------------------------------
# audit command
# ---------------------------------------------------------------------------

def test_audit_all_clean_exits_zero(tmp_env):
    ref = tmp_env(".env.example", "FOO=1\nBAR=2\n")
    t1 = tmp_env(".env.staging", "FOO=1\nBAR=2\n")
    t2 = tmp_env(".env.prod", "FOO=1\nBAR=2\n")
    assert main(["audit", ref, t1, t2, "--no-color"]) == 0


def test_audit_one_bad_target_exits_one(tmp_env):
    ref = tmp_env(".env.example", "FOO=1\nBAR=2\n")
    t1 = tmp_env(".env.staging", "FOO=1\nBAR=2\n")
    t2 = tmp_env(".env.prod", "FOO=1\n")  # missing BAR
    assert main(["audit", ref, t1, t2, "--no-color"]) == 1


def test_audit_prints_report_per_target(tmp_env, capsys):
    ref = tmp_env(".env.example", "FOO=1\n")
    t1 = tmp_env(".env.staging", "FOO=1\n")
    t2 = tmp_env(".env.prod", "FOO=1\n")
    main(["audit", ref, t1, t2, "--no-color"])
    out = capsys.readouterr().out
    assert ".env.staging" in out
    assert ".env.prod" in out
