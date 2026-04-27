"""Diff engine for comparing .env files across environments."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class DiffStatus(str, Enum):
    MISSING = "missing"
    EXTRA = "extra"
    MISMATCH = "mismatch"
    OK = "ok"


@dataclass
class DiffEntry:
    key: str
    status: DiffStatus
    base_value: Optional[str] = None
    target_value: Optional[str] = None

    def __repr__(self) -> str:
        return (
            f"DiffEntry(key={self.key!r}, status={self.status.value}, "
            f"base={self.base_value!r}, target={self.target_value!r})"
        )


@dataclass
class DiffResult:
    base_name: str
    target_name: str
    entries: List[DiffEntry] = field(default_factory=list)

    @property
    def missing(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.MISSING]

    @property
    def extra(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.EXTRA]

    @property
    def mismatched(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.MISMATCH]

    @property
    def ok(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.OK]

    @property
    def has_issues(self) -> bool:
        return bool(self.missing or self.extra or self.mismatched)


def diff_envs(
    base: Dict[str, str],
    target: Dict[str, str],
    base_name: str = "base",
    target_name: str = "target",
    check_values: bool = False,
) -> DiffResult:
    """Compare two parsed env dicts and return a DiffResult.

    Args:
        base: The reference environment (e.g. .env.example).
        target: The environment under audit (e.g. .env).
        base_name: Label for the base env.
        target_name: Label for the target env.
        check_values: If True, also flag keys whose values differ.
    """
    result = DiffResult(base_name=base_name, target_name=target_name)
    all_keys = sorted(set(base) | set(target))

    for key in all_keys:
        in_base = key in base
        in_target = key in target

        if in_base and not in_target:
            result.entries.append(DiffEntry(key=key, status=DiffStatus.MISSING, base_value=base[key]))
        elif in_target and not in_base:
            result.entries.append(DiffEntry(key=key, status=DiffStatus.EXTRA, target_value=target[key]))
        elif check_values and base[key] != target[key]:
            result.entries.append(
                DiffEntry(key=key, status=DiffStatus.MISMATCH, base_value=base[key], target_value=target[key])
            )
        else:
            result.entries.append(
                DiffEntry(key=key, status=DiffStatus.OK, base_value=base[key], target_value=target[key])
            )

    return result
