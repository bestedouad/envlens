"""Parser module for reading and parsing .env files."""

import re
from pathlib import Path
from typing import Dict, Optional


ENV_LINE_PATTERN = re.compile(
    r"^\s*(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)\s*$"
)
COMMENT_PATTERN = re.compile(r"^\s*#.*$")


class EnvParseError(Exception):
    """Raised when an .env file cannot be parsed."""


def parse_env_file(filepath: str) -> Dict[str, Optional[str]]:
    """
    Parse a .env file and return a dict of key-value pairs.

    - Ignores blank lines and comments.
    - Strips inline comments after values.
    - Handles quoted values (single and double quotes).

    Args:
        filepath: Path to the .env file.

    Returns:
        A dictionary mapping variable names to their values.

    Raises:
        FileNotFoundError: If the file does not exist.
        EnvParseError: If a non-comment, non-blank line is malformed.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    env_vars: Dict[str, Optional[str]] = {}

    with path.open("r", encoding="utf-8") as fh:
        for lineno, raw_line in enumerate(fh, start=1):
            line = raw_line.rstrip("\n")

            if not line.strip() or COMMENT_PATTERN.match(line):
                continue

            match = ENV_LINE_PATTERN.match(line)
            if not match:
                raise EnvParseError(
                    f"Malformed line {lineno} in '{filepath}': {line!r}"
                )

            key = match.group("key")
            raw_value = match.group("value").strip()
            value = _strip_quotes_and_comments(raw_value)
            env_vars[key] = value

    return env_vars


def _strip_quotes_and_comments(value: str) -> Optional[str]:
    """Remove surrounding quotes and trailing inline comments from a value."""
    if not value:
        return ""

    # Handle quoted values
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]

    # Strip inline comment (unquoted values)
    comment_index = value.find(" #")
    if comment_index != -1:
        value = value[:comment_index].strip()

    return value
