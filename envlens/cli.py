"""Entry-point for the envlens CLI."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from envlens.audit import audit_and_report, audit_many
from envlens.cli_snapshot import add_snapshot_subparser, handle_snapshot
from envlens.cli_template import add_template_subparser, handle_template
from envlens.differ import diff_env_files
from envlens.exporter import export_result
from envlens.merger import merge_env_files
from envlens.reporter import format_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envlens",
        description="Audit and diff .env files across environments.",
    )
    sub = parser.add_subparsers(dest="command")

    # diff
    diff_p = sub.add_parser("diff", help="Diff two .env files.")
    diff_p.add_argument("base", help="Base .env file.")
    diff_p.add_argument("compare", help="Comparison .env file.")
    diff_p.add_argument("--check-values", action="store_true", default=False)
    diff_p.add_argument("--format", choices=["text", "json", "csv", "markdown"], default="text")
    diff_p.add_argument("--output", default=None)

    # audit
    audit_p = sub.add_parser("audit", help="Audit one or more .env files against a base.")
    audit_p.add_argument("base", help="Base .env file.")
    audit_p.add_argument("targets", nargs="+", help=".env files to audit.")
    audit_p.add_argument("--check-values", action="store_true", default=False)
    audit_p.add_argument("--format", choices=["text", "json", "csv", "markdown"], default="text")

    # merge
    merge_p = sub.add_parser("merge", help="Merge multiple .env files.")
    merge_p.add_argument("files", nargs="+", help=".env files to merge (later files win).")
    merge_p.add_argument("--output", default=None, help="Write merged output to file.")

    # snapshot + template
    add_snapshot_subparser(sub)
    add_template_subparser(sub)

    return parser


def _handle_diff(args: argparse.Namespace) -> int:
    result = diff_env_files(args.base, args.compare, check_values=args.check_values)
    fmt = args.format
    if fmt == "text":
        report = format_report(result, args.base, args.compare)
        if args.output:
            Path(args.output).write_text(report, encoding="utf-8")
        else:
            print(report)
    else:
        content = export_result(result, fmt)  # type: ignore[arg-type]
        if args.output:
            Path(args.output).write_text(content, encoding="utf-8")
        else:
            print(content)
    return 0 if result.is_clean else 1


def _handle_audit(args: argparse.Namespace) -> int:
    exit_code = 0
    for target in args.targets:
        result = audit_and_report(
            args.base,
            target,
            check_values=args.check_values,
            fmt=args.format,  # type: ignore[arg-type]
        )
        print(result)
        if not diff_env_files(args.base, target, check_values=args.check_values).is_clean:
            exit_code = 1
    return exit_code


def _handle_merge(args: argparse.Namespace) -> int:
    merge_result = merge_env_files(args.files)
    lines = [f"{k}={v}" for k, v in merge_result.merged.items()]
    content = "\n".join(lines) + "\n"
    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
        print(f"Merged {len(args.files)} files -> {args.output}")
    else:
        print(content)
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "diff":
        return _handle_diff(args)
    if args.command == "audit":
        return _handle_audit(args)
    if args.command == "merge":
        return _handle_merge(args)
    if args.command == "snapshot":
        return handle_snapshot(args)
    if args.command == "template":
        return handle_template(args)

    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
