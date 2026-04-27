"""High-level audit API — ties parser, differ, and reporter together."""

from pathlib import Path
from typing import List, Optional, Tuple

from envlens.differ import DiffResult, diff_envs
from envlens.parser import parse_env_file
from envlens.reporter import format_report


def audit_files(
    base_path: str | Path,
    target_path: str | Path,
    check_values: bool = False,
) -> DiffResult:
    """Parse two .env files and return a DiffResult.

    Args:
        base_path: Path to the reference file (e.g. .env.example).
        target_path: Path to the file being audited (e.g. .env).
        check_values: Whether to flag value mismatches.

    Returns:
        A DiffResult describing the differences.
    """
    base_path = Path(base_path)
    target_path = Path(target_path)

    base_env = parse_env_file(base_path)
    target_env = parse_env_file(target_path)

    return diff_envs(
        base=base_env,
        target=target_env,
        base_name=base_path.name,
        target_name=target_path.name,
        check_values=check_values,
    )


def audit_and_report(
    base_path: str | Path,
    target_path: str | Path,
    check_values: bool = False,
    use_color: bool = True,
    show_ok: bool = False,
) -> Tuple[str, bool]:
    """Audit two env files and return a rendered report and a success flag.

    Returns:
        A tuple of (report_string, ok) where ok is True when no issues exist.
    """
    result = audit_files(base_path, target_path, check_values=check_values)
    report = format_report(result, use_color=use_color, show_ok=show_ok)
    return report, not result.has_issues


def audit_many(
    base_path: str | Path,
    target_paths: List[str | Path],
    check_values: bool = False,
) -> List[DiffResult]:
    """Audit multiple target files against a single base.

    Args:
        base_path: Path to the reference file.
        target_paths: List of paths to audit.
        check_values: Whether to flag value mismatches.

    Returns:
        A list of DiffResult objects, one per target.
    """
    return [audit_files(base_path, t, check_values=check_values) for t in target_paths]
