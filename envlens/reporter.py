"""Formatters for rendering DiffResult to the terminal."""

from typing import Optional

from envlens.differ import DiffResult, DiffStatus

TERMINAL_COLORS = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    "bold": "\033[1m",
    "reset": "\033[0m",
}


def _color(text: str, color: str, use_color: bool = True) -> str:
    if not use_color:
        return text
    code = TERMINAL_COLORS.get(color, "")
    reset = TERMINAL_COLORS["reset"]
    return f"{code}{text}{reset}"


def format_report(result: DiffResult, use_color: bool = True, show_ok: bool = False) -> str:
    """Render a DiffResult as a human-readable string."""
    lines = []
    header = f"Diff: {result.base_name!r} → {result.target_name!r}"
    lines.append(_color(header, "bold", use_color))
    lines.append("-" * len(header))

    if not result.has_issues and not show_ok:
        lines.append(_color("✔  No issues found.", "green", use_color))
        return "\n".join(lines)

    for entry in result.entries:
        if entry.status == DiffStatus.MISSING:
            msg = f"  MISSING  {entry.key}"
            lines.append(_color(msg, "red", use_color))
        elif entry.status == DiffStatus.EXTRA:
            msg = f"  EXTRA    {entry.key}"
            lines.append(_color(msg, "yellow", use_color))
        elif entry.status == DiffStatus.MISMATCH:
            msg = f"  MISMATCH {entry.key}  (base={entry.base_value!r}, target={entry.target_value!r})"
            lines.append(_color(msg, "cyan", use_color))
        elif show_ok:
            msg = f"  OK       {entry.key}"
            lines.append(_color(msg, "green", use_color))

    summary_parts = []
    if result.missing:
        summary_parts.append(_color(f"{len(result.missing)} missing", "red", use_color))
    if result.extra:
        summary_parts.append(_color(f"{len(result.extra)} extra", "yellow", use_color))
    if result.mismatched:
        summary_parts.append(_color(f"{len(result.mismatched)} mismatched", "cyan", use_color))
    if result.ok and show_ok:
        summary_parts.append(_color(f"{len(result.ok)} ok", "green", use_color))

    lines.append("")
    lines.append("Summary: " + ", ".join(summary_parts) if summary_parts else "Summary: all ok")
    return "\n".join(lines)
