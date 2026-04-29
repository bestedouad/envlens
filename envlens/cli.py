"""Command-line interface for envlens."""
from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from envlens.audit import audit_and_report, audit_many
from envlens.exporter import export_result
from envlens.merger import merge_env_files
from envlens.parser import EnvParseError


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="envlens",
        description="Audit and diff .env files across environments.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── diff ──────────────────────────────────────────────────────────────────
    diff_p = sub.add_parser("diff", help="Diff two .env files.")
    diff_p.add_argument("reference", help="Reference .env file (expected keys).")
    diff_p.add_argument("target", help="Target .env file to audit.")
    diff_p.add_argument(
        "--check-values",
        action="store_true",
        default=False,
        help="Also flag keys whose values differ.",
    )
    diff_p.add_argument(
        "--export",
        choices=["json", "csv", "markdown"],
        default=None,
        help="Export diff result in the given format.",
    )
    diff_p.add_argument(
        "--no-color", action="store_true", default=False, help="Disable ANSI colours."
    )

    # ── audit ─────────────────────────────────────────────────────────────────
    audit_p = sub.add_parser("audit", help="Audit multiple .env files against a reference.")
    audit_p.add_argument("reference", help="Reference .env file.")
    audit_p.add_argument("targets", nargs="+", help="One or more target .env files.")
    audit_p.add_argument("--check-values", action="store_true", default=False)
    audit_p.add_argument("--no-color", action="store_true", default=False)

    # ── merge ─────────────────────────────────────────────────────────────────
    merge_p = sub.add_parser(
        "merge",
        help="Merge .env files (last file wins) and print the result.",
    )
    merge_p.add_argument("files", nargs="+", help=".env files to merge in order.")
    merge_p.add_argument(
        "--show-overrides",
        action="store_true",
        default=False,
        help="Print keys that were overridden by a later file.",
    )

    return parser


def _handle_diff(args: Namespace) -> int:
    try:
        report = audit_and_report(
            args.reference,
            args.target,
            check_values=args.check_values,
            color=not args.no_color,
        )
    except EnvParseError as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        return 2

    if args.export:
        from envlens.audit import audit_files

        result = audit_files(args.reference, args.target, check_values=args.check_values)
        print(export_result(result, fmt=args.export))
    else:
        print(report.text)

    return 0 if report.ok else 1


def _handle_audit(args: Namespace) -> int:
    results = audit_many(
        args.reference,
        args.targets,
        check_values=args.check_values,
    )
    exit_code = 0
    for path, result in results.items():
        header = f"=== {path} ==="
        print(header)
        from envlens.reporter import format_report

        print(format_report(result, color=not args.no_color))
        if not result.ok:
            exit_code = 1
    return exit_code


def _handle_merge(args: Namespace) -> int:
    try:
        result = merge_env_files(*args.files)
    except EnvParseError as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        return 2

    for key, value in sorted(result.merged.items()):
        print(f"{key}={value}")

    if args.show_overrides and result.overridden_keys:
        print("\n# Overridden keys:", file=sys.stderr)
        for key in sorted(result.overridden_keys):
            print(f"#  {key} (from {result.source_for(key)})", file=sys.stderr)

    return 0


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    handlers = {
        "diff": _handle_diff,
        "audit": _handle_audit,
        "merge": _handle_merge,
    }
    sys.exit(handlers[args.command](args))


if __name__ == "__main__":  # pragma: no cover
    main()
