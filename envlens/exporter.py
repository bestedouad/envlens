"""Export diff results to various output formats (JSON, CSV, Markdown)."""

from __future__ import annotations

import csv
import io
import json
from typing import Literal

from envlens.differ import DiffResult, DiffStatus

OutputFormat = Literal["json", "csv", "markdown"]


def export_result(result: DiffResult, fmt: OutputFormat) -> str:
    """Serialize a DiffResult to the requested format string."""
    if fmt == "json":
        return _to_json(result)
    if fmt == "csv":
        return _to_csv(result)
    if fmt == "markdown":
        return _to_markdown(result)
    raise ValueError(f"Unsupported export format: {fmt!r}")


def _entry_dict(entry) -> dict:
    return {
        "key": entry.key,
        "status": entry.status.value,
        "reference_value": entry.reference_value,
        "target_value": entry.target_value,
    }


def _to_json(result: DiffResult) -> str:
    payload = {
        "reference": result.reference_file,
        "target": result.target_file,
        "has_issues": result.has_issues,
        "entries": [_entry_dict(e) for e in result.entries],
    }
    return json.dumps(payload, indent=2)


def _to_csv(result: DiffResult) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=["key", "status", "reference_value", "target_value"],
        lineterminator="\n",
    )
    writer.writeheader()
    for entry in result.entries:
        writer.writerow(_entry_dict(entry))
    return buf.getvalue()


def _to_markdown(result: DiffResult) -> str:
    lines = [
        f"## envlens diff: `{result.reference_file}` vs `{result.target_file}`",
        "",
        "| Key | Status | Reference Value | Target Value |",
        "|-----|--------|----------------|--------------|",
    ]
    for entry in result.entries:
        ref = entry.reference_value or ""
        tgt = entry.target_value or ""
        lines.append(f"| `{entry.key}` | {entry.status.value} | {ref} | {tgt} |")
    lines.append("")
    status_line = "✅ No issues found." if not result.has_issues else "❌ Issues detected."
    lines.append(status_line)
    return "\n".join(lines)
