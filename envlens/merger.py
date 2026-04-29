"""Merge multiple .env files into a single resolved output.

Later files take precedence over earlier ones (last-write-wins).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from envlens.parser import parse_env_file


@dataclass
class MergeResult:
    """Outcome of merging two or more .env files."""

    merged: Dict[str, str] = field(default_factory=dict)
    # key -> list of (source_path, value) in resolution order
    provenance: Dict[str, List[Tuple[str, str]]] = field(default_factory=dict)

    @property
    def overridden_keys(self) -> List[str]:
        """Keys whose value was overridden by at least one later file."""
        return [k for k, sources in self.provenance.items() if len(sources) > 1]

    def source_for(self, key: str) -> Optional[str]:
        """Return the path of the file that provided the final value for *key*."""
        sources = self.provenance.get(key)
        return sources[-1][0] if sources else None


def merge_env_files(
    *paths: str | Path,
    keep_all: bool = False,
) -> MergeResult:
    """Merge .env files in order; later files override earlier ones.

    Parameters
    ----------
    *paths:
        One or more paths to .env files, processed left-to-right.
    keep_all:
        If *True*, keys present only in earlier files are retained even when a
        later file does not define them (default behaviour).  When *False* the
        semantics are identical — this flag is reserved for future filtering.

    Returns
    -------
    MergeResult
    """
    result = MergeResult()

    for raw_path in paths:
        path = Path(raw_path)
        pairs = parse_env_file(path)
        for key, value in pairs.items():
            if key not in result.provenance:
                result.provenance[key] = []
            result.provenance[key].append((str(path), value))
            result.merged[key] = value  # last-write-wins

    return result
