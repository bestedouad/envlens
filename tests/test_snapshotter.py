"""Tests for envlens.snapshotter."""
from __future__ import annotations

import json
import os
import pytest

from envlens.snapshotter import (
    Snapshot,
    SnapshotError,
    capture,
    diff_snapshots,
    load_snapshot,
    save_snapshot,
)


@pytest.fixture()
def tmp_dir(tmp_path):
    return tmp_path


# ── capture ───────────────────────────────────────────────────────────────────

def test_capture_stores_variables():
    snap = capture("/app/.env", {"KEY": "val"})
    assert snap.variables == {"KEY": "val"}


def test_capture_records_absolute_path(tmp_dir):
    env_file = tmp_dir / ".env"
    env_file.write_text("X=1\n")
    snap = capture(str(env_file), {"X": "1"})
    assert os.path.isabs(snap.path)


def test_capture_sets_captured_at():
    snap = capture("/app/.env", {})
    assert "T" in snap.captured_at  # ISO-8601 contains 'T'


# ── save / load round-trip ────────────────────────────────────────────────────

def test_save_creates_json_file(tmp_dir):
    snap = capture("/app/.env", {"A": "1"})
    dest = str(tmp_dir / "snap.json")
    save_snapshot(snap, dest)
    assert os.path.exists(dest)
    with open(dest) as fh:
        data = json.load(fh)
    assert data["variables"] == {"A": "1"}


def test_load_round_trips_snapshot(tmp_dir):
    snap = capture("/app/.env", {"DB": "postgres"})
    dest = str(tmp_dir / "snap.json")
    save_snapshot(snap, dest)
    loaded = load_snapshot(dest)
    assert loaded.variables == snap.variables
    assert loaded.path == snap.path


def test_load_raises_on_missing_file(tmp_dir):
    with pytest.raises(SnapshotError, match="Could not read"):
        load_snapshot(str(tmp_dir / "nonexistent.json"))


def test_load_raises_on_malformed_json(tmp_dir):
    bad = tmp_dir / "bad.json"
    bad.write_text("not json")
    with pytest.raises(SnapshotError):
        load_snapshot(str(bad))


def test_load_raises_on_missing_field(tmp_dir):
    broken = tmp_dir / "broken.json"
    broken.write_text(json.dumps({"path": "/x", "captured_at": "now"}))
    with pytest.raises(SnapshotError, match="missing field"):
        load_snapshot(str(broken))


# ── diff_snapshots ────────────────────────────────────────────────────────────

def test_diff_detects_added_key():
    old = Snapshot("/e", "t", {"A": "1"})
    new = Snapshot("/e", "t", {"A": "1", "B": "2"})
    diff = diff_snapshots(old, new)
    assert diff["added"] == {"B": "2"}
    assert diff["removed"] == {}


def test_diff_detects_removed_key():
    old = Snapshot("/e", "t", {"A": "1", "B": "2"})
    new = Snapshot("/e", "t", {"A": "1"})
    diff = diff_snapshots(old, new)
    assert diff["removed"] == {"B": "2"}


def test_diff_detects_changed_value():
    old = Snapshot("/e", "t", {"PORT": "8000"})
    new = Snapshot("/e", "t", {"PORT": "9000"})
    diff = diff_snapshots(old, new)
    assert diff["changed"] == {"PORT": {"old": "8000", "new": "9000"}}


def test_diff_empty_when_identical():
    snap = Snapshot("/e", "t", {"X": "1"})
    diff = diff_snapshots(snap, snap)
    assert diff == {"added": {}, "removed": {}, "changed": {}}
