"""CLI entry-point for envlens."""

from __future__ import annotations

import argparse
import sys

from envlens.audit import audit_and_report, audit_files
from envlens.exporter import OutputFormat, export_result
from envlens.reporter import format_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envlens",
        description="Audit and diff .env files across environments.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── diff ──────────────────────────────────────────────────────────────────
    diff_p = sub.add_parser("diff", help="Diff two .env files.")
    diff_p.add_argument("reference", help="Reference .env file (e.g. .env.example)")
    diff_p.add_argument("target", help="Target .env file to audit")
    diff_p.add_argument(
        "--check-values",
        action="store_true",
        default=False,
        help="Also flag mismatched values (not just missing/extra keys).",
    )
    diff_p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    diff_p.add_argument(
        "--export",
        choices=["json", "csv", "markdown"],
        default=None,
        metavar="FORMAT",
        help="Export diff result to FORMAT (json, csv, markdown) instead of the default report.",
    )

    # ── audit ─────────────────────────────────────────────────────────────────
    audit_p = sub.add_parser("audit", help="Audit multiple .env files against a reference.")
    audit_p.add_argument("reference", help="Reference .env file")
    audit_p.add_argument("targets", nargs="+", help="One or more target .env files")
    audit_p.add_argument("--check-values", action="store_true", default=False)
    audit_p.add_argument("--no-color", action="store_true", default=False)
    audit_p.add_argument(
        "--export",
        choices=["json", "csv", "markdown"],
        default=None,
        metavar="FORMAT",
    )

    return parser


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args(argv)

    use_color = not args.no_color
    exit_code = 0

    if args.command == "diff":
        result = audit_files(
            args.reference,
            args.target,
            check_values=args.check_values,
        )
        if args.export:
            print(export_result(result, args.export))  # type: ignore[arg-type]
        else:
            print(format_report(result, color=use_color))
        if result.has_issues:
            exit_code = 1

    elif args.command == "audit":
        has_any_issues = False
        for target in args.targets:
            result = audit_files(args.reference, target, check_values=args.check_values)
            if args.export:
                print(export_result(result, args.export))  # type: ignore[arg-type]
            else:
                print(format_report(result, color=use_color))
            if result.has_issues:
                has_any_issues = True
        if has_any_issues:
            exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()
