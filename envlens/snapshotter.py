"""Snapshot support: save and load .env audit snapshots for later comparison."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional


class SnapshotError(Exception):
    """Raised when a snapshot cannot be saved or loaded."""


@dataclass
class Snapshot:
    """A point-in-time record of an env file's key/value pairs."""

    path: str
    captured_at: str
    variables: Dict[str, str]

    def keys(self) -> List[str]:
        return list(self.variables.keys())


def capture(env_path: str, variables: Dict[str, str]) -> Snapshot:
    """Create a Snapshot from a parsed env mapping."""
    return Snapshot(
        path=os.path.abspath(env_path),
        captured_at=datetime.now(timezone.utc).isoformat(),
        variables=dict(variables),
    )


def save_snapshot(snapshot: Snapshot, dest: str) -> None:
    """Persist *snapshot* as JSON to *dest*."""
    try:
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(asdict(snapshot), fh, indent=2)
    except OSError as exc:
        raise SnapshotError(f"Could not write snapshot to {dest!r}: {exc}") from exc


def load_snapshot(src: str) -> Snapshot:
    """Load a previously saved snapshot from *src*."""
    try:
        with open(src, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"Could not read snapshot from {src!r}: {exc}") from exc

    try:
        return Snapshot(
            path=data["path"],
            captured_at=data["captured_at"],
            variables=data["variables"],
        )
    except KeyError as exc:
        raise SnapshotError(f"Snapshot file {src!r} is missing field {exc}") from exc


def diff_snapshots(
    old: Snapshot, new: Snapshot
) -> Dict[str, object]:
    """Return a simple diff dict between two snapshots."""
    old_vars = old.variables
    new_vars = new.variables
    added = {k: new_vars[k] for k in new_vars if k not in old_vars}
    removed = {k: old_vars[k] for k in old_vars if k not in new_vars}
    changed = {
        k: {"old": old_vars[k], "new": new_vars[k]}
        for k in old_vars
        if k in new_vars and old_vars[k] != new_vars[k]
    }
    return {"added": added, "removed": removed, "changed": changed}
