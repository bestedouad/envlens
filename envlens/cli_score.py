"""CLI subcommand: envlens score — print a health score for a .env file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envlens.parser import parse_env_file, EnvParseError
from envlens.linter import lint_env
from envlens.validator import validate
from envlens.redactor import redact
from envlens.scorer import score_env, ScoreResult


def add_score_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "score",
        help="Score the health of a .env file (0-100)",
    )
    p.add_argument("file", help="Path to the .env file to score")
    p.add_argument(
        "--required",
        nargs="*",
        metavar="KEY",
        default=[],
        help="Keys that must be present (validation)",
    )
    p.add_argument(
        "--no-lint",
        action="store_true",
        help="Skip lint checks",
    )
    p.add_argument(
        "--no-redact",
        action="store_true",
        help="Skip redaction/sensitive-key checks",
    )
    p.set_defaults(func=handle_score)


def handle_score(args: argparse.Namespace) -> int:
    path = Path(args.file)

    try:
        variables = parse_env_file(path)
    except EnvParseError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError:
        print(f"[error] File not found: {path}", file=sys.stderr)
        return 2
    except PermissionError:
        print(f"[error] Permission denied: {path}", file=sys.stderr)
        return 2

    lint_result = None if args.no_lint else lint_env(variables)

    validation_result = None
    if args.required:
        rules = {"required": args.required}
        validation_result = validate(variables, rules)

    redact_result = None if args.no_redact else redact(variables)

    result: ScoreResult = score_env(
        lint_result=lint_result,
        validation_result=validation_result,
        redact_result=redact_result,
    )

    _print_report(path, result)

    return 0 if result.score >= 60 else 1


def _print_report(path: Path, result: ScoreResult) -> None:
    print(f"\nHealth Score for: {path}")
    print(f"  Score : {result.score}/100")
    print(f"  Grade : {result.grade}")
    if result.breakdown.lint_penalty:
        print(f"  Lint  : -{result.breakdown.lint_penalty} pts")
    if result.breakdown.validation_penalty:
        print(f"  Valid : -{result.breakdown.validation_penalty} pts")
    if result.breakdown.redaction_penalty:
        print(f"  Redact: -{result.breakdown.redaction_penalty} pts")
    if result.notes:
        print("  Notes :")
        for note in result.notes:
            print(f"    - {note}")
    print()
