"""Command-line interface for envlens."""

import sys
import argparse

from envlens.audit import audit_and_report, audit_many


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envlens",
        description="Audit and diff .env files across environments.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- diff command ---
    diff_cmd = subparsers.add_parser(
        "diff",
        help="Diff two .env files and report missing or mismatched variables.",
    )
    diff_cmd.add_argument("reference", help="Reference .env file (e.g. .env.example)")
    diff_cmd.add_argument("target", help="Target .env file to audit (e.g. .env)")
    diff_cmd.add_argument(
        "--check-values",
        action="store_true",
        default=False,
        help="Also report variables whose values differ between files.",
    )
    diff_cmd.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI color output.",
    )

    # --- audit command ---
    audit_cmd = subparsers.add_parser(
        "audit",
        help="Audit multiple .env files against a single reference.",
    )
    audit_cmd.add_argument("reference", help="Reference .env file (e.g. .env.example)")
    audit_cmd.add_argument("targets", nargs="+", help="One or more target .env files.")
    audit_cmd.add_argument(
        "--check-values",
        action="store_true",
        default=False,
    )
    audit_cmd.add_argument("--no-color", action="store_true", default=False)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    use_color = not args.no_color

    if args.command == "diff":
        report, has_issues = audit_and_report(
            args.reference,
            args.target,
            check_values=args.check_values,
            use_color=use_color,
        )
        print(report)
        return 1 if has_issues else 0

    if args.command == "audit":
        exit_code = 0
        for report, has_issues in audit_many(
            args.reference,
            args.targets,
            check_values=args.check_values,
            use_color=use_color,
        ):
            print(report)
            if has_issues:
                exit_code = 1
        return exit_code

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
