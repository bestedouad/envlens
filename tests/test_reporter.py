"""Tests for envlens.reporter."""

from envlens.differ import diff_envs
from envlens.reporter import format_report


BASE = {"DB_HOST": "localhost", "SECRET_KEY": "changeme"}
TARGET = {"DB_HOST": "prod", "EXTRA_VAR": "extra"}


def _plain(result, **kwargs):
    return format_report(result, use_color=False, **kwargs)


def test_report_contains_header():
    result = diff_envs(BASE, TARGET, base_name=".env.example", target_name=".env")
    report = _plain(result)
    assert ".env.example" in report
    assert ".env" in report


def test_report_shows_missing():
    result = diff_envs(BASE, TARGET)
    report = _plain(result)
    assert "MISSING" in report
    assert "SECRET_KEY" in report


def test_report_shows_extra():
    result = diff_envs(BASE, TARGET)
    report = _plain(result)
    assert "EXTRA" in report
    assert "EXTRA_VAR" in report


def test_report_shows_mismatch():
    result = diff_envs(BASE, {"DB_HOST": "prod", "SECRET_KEY": "other"}, check_values=True)
    report = _plain(result)
    assert "MISMATCH" in report
    assert "DB_HOST" in report


def test_report_no_issues_message():
    result = diff_envs(BASE, BASE)
    report = _plain(result)
    assert "No issues found" in report


def test_report_show_ok_flag():
    result = diff_envs(BASE, BASE)
    report = _plain(result, show_ok=True)
    assert "OK" in report


def test_report_summary_line():
    result = diff_envs(BASE, TARGET)
    report = _plain(result)
    assert "Summary" in report
    assert "missing" in report
    assert "extra" in report


def test_color_codes_present_by_default():
    result = diff_envs(BASE, TARGET)
    report = format_report(result, use_color=True)
    assert "\033[" in report


def test_no_color_codes_when_disabled():
    result = diff_envs(BASE, TARGET)
    report = format_report(result, use_color=False)
    assert "\033[" not in report
