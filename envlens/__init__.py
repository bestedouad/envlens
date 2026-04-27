"""envlens — Audit and diff .env files across environments."""

__version__ = "0.1.0"
__author__ = "envlens contributors"

from envlens.parser import parse_env_file, EnvParseError

__all__ = ["parse_env_file", "EnvParseError"]
