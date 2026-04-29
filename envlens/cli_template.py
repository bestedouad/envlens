"""CLI subcommand: template — generate a .env.example from a .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envlens.templater import render_template, save_template


def add_template_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *template* subcommand on *subparsers*."""
    p = subparsers.add_parser(
        "template",
        help="Generate a .env.example template from a .env file.",
    )
    p.add_argument("source", help="Path to the source .env file.")
    p.add_argument(
        "-o",
        "--output",
        default=None,
        help="Write template to this file (default: print to stdout).",
    )
    p.add_argument(
        "--placeholder",
        default="",
        help="Value to use for every variable (default: empty string).",
    )
    p.add_argument(
        "--no-comments",
        action="store_true",
        default=False,
        help="Omit the header comment block.",
    )


def handle_template(args: argparse.Namespace) -> int:
    """Execute the *template* subcommand and return an exit code."""
    source = Path(args.source)
    if not source.exists():
        print(f"envlens template: file not found: {source}", file=sys.stderr)
        return 2

    include_comments = not args.no_comments

    if args.output:
        result = save_template(
            source,
            args.output,
            placeholder=args.placeholder,
            include_comments=include_comments,
        )
        print(f"Template written to {result.output_path} ({len(result.keys)} keys).")
    else:
        rendered = render_template(
            source,
            placeholder=args.placeholder,
            include_comments=include_comments,
        )
        sys.stdout.write(rendered)

    return 0
