"""Tests for envlens.exporter — JSON, CSV, and Markdown export."""

from __future__ import annotations

import csv
import io
import json

import pytest

from envlens.differ import DiffEntry, DiffResult, DiffStatus
from envlens.exporter import export_result


def _result(entries=None):
    return DiffResult(
        reference_file=".env.example",
        target_file=".env",
        entries=entries or [],
    )


def _missing(key):
    return DiffEntry(key=key, status=DiffStatus.MISSING, reference_value="val", target_value=None)


def _extra(key):
    return DiffEntry(key=key, status=DiffStatus.EXTRA, reference_value=None, target_value="val")


def _mismatch(key):
    return DiffEntry(key=key, status=DiffStatus.MISMATCH, reference_value="a", target_value="b")


# ── JSON ──────────────────────────────────────────────────────────────────────

def test_json_export_structure():
    result = _result([_missing("DB_URL")])
    data = json.loads(export_result(result, "json"))
    assert data["reference"] == ".env.example"
    assert data["target"] == ".env"
    assert data["has_issues"] is True
    assert len(data["entries"]) == 1
    assert data["entries"][0]["key"] == "DB_URL"
    assert data["entries"][0]["status"] == "missing"


def test_json_export_no_issues():
    data = json.loads(export_result(_result(), "json"))
    assert data["has_issues"] is False
    assert data["entries"] == []


# ── CSV ───────────────────────────────────────────────────────────────────────

def test_csv_export_has_header_and_rows():
    result = _result([_extra("SECRET"), _mismatch("PORT")])
    raw = export_result(result, "csv")
    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["key"] == "SECRET"
    assert rows[0]["status"] == "extra"
    assert rows[1]["key"] == "PORT"
    assert rows[1]["status"] == "mismatch"


def test_csv_export_empty_entries():
    raw = export_result(_result(), "csv")
    reader = csv.DictReader(io.StringIO(raw))
    assert list(reader) == []


# ── Markdown ──────────────────────────────────────────────────────────────────

def test_markdown_export_contains_header():
    raw = export_result(_result(), "markdown")
    assert "## envlens diff" in raw
    assert ".env.example" in raw
    assert ".env" in raw


def test_markdown_export_no_issues_message():
    raw = export_result(_result(), "markdown")
    assert "✅ No issues found." in raw


def test_markdown_export_issues_message():
    raw = export_result(_result([_missing("API_KEY")]), "markdown")
    assert "❌ Issues detected." in raw
    assert "API_KEY" in raw


# ── Invalid format ────────────────────────────────────────────────────────────

def test_invalid_format_raises():
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_result(_result(), "xml")  # type: ignore[arg-type]
