"""CLI helpers for the 'snapshot' sub-command."""
from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace
from typing import List

from .parser import parse_env_file
from .snapshotter import (
    SnapshotError,
    capture,
    diff_snapshots,
    load_snapshot,
    save_snapshot,
)


def add_snapshot_subparser(subparsers) -> None:  # type: ignore[type-arg]
    """Register 'snapshot' sub-commands onto *subparsers*."""
    sp = subparsers.add_parser(
        "snapshot", help="Capture or compare .env snapshots"
    )
    sub = sp.add_subparsers(dest="snapshot_cmd", required=True)

    # snapshot save
    save_p = sub.add_parser("save", help="Save a snapshot of an env file")
    save_p.add_argument("env_file", help="Path to the .env file")
    save_p.add_argument("output", help="Destination JSON snapshot file")

    # snapshot diff
    diff_p = sub.add_parser("diff", help="Diff two snapshot files")
    diff_p.add_argument("old_snapshot", help="Older snapshot JSON")
    diff_p.add_argument("new_snapshot", help="Newer snapshot JSON")
    diff_p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
    )


def handle_snapshot(args: Namespace) -> int:
    """Dispatch snapshot sub-command; return exit code."""
    if args.snapshot_cmd == "save":
        return _do_save(args)
    if args.snapshot_cmd == "diff":
        return _do_diff(args)
    return 1


def _do_save(args: Namespace) -> int:
    try:
        variables = parse_env_file(args.env_file)
        snap = capture(args.env_file, variables)
        save_snapshot(snap, args.output)
        print(f"Snapshot saved to {args.output}")
        return 0
    except (SnapshotError, Exception) as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _do_diff(args: Namespace) -> int:
    try:
        old = load_snapshot(args.old_snapshot)
        new = load_snapshot(args.new_snapshot)
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    diff = diff_snapshots(old, new)
    has_changes = any(diff[k] for k in ("added", "removed", "changed"))

    if args.fmt == "json":
        print(json.dumps(diff, indent=2))
    else:
        if not has_changes:
            print("No changes between snapshots.")
        for k, v in diff["added"].items():
            print(f"+ {k}={v}")
        for k, v in diff["removed"].items():
            print(f"- {k}={v}")
        for k, info in diff["changed"].items():
            print(f"~ {k}: {info['old']!r} -> {info['new']!r}")

    return 1 if has_changes else 0
