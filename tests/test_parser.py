"""Tests for envlens.parser module."""

import pytest
from pathlib import Path

from envlens.parser import parse_env_file, EnvParseError


@pytest.fixture
def tmp_env(tmp_path):
    """Helper fixture that writes content to a temp .env file and returns its path."""
    def _write(content: str) -> str:
        env_file = tmp_path / ".env"
        env_file.write_text(content, encoding="utf-8")
        return str(env_file)
    return _write


def test_parses_simple_key_value(tmp_env):
    path = tmp_env("APP_ENV=production\nDEBUG=false\n")
    result = parse_env_file(path)
    assert result == {"APP_ENV": "production", "DEBUG": "false"}


def test_ignores_comments_and_blank_lines(tmp_env):
    content = "# This is a comment\n\nDB_HOST=localhost\n"
    path = tmp_env(content)
    result = parse_env_file(path)
    assert result == {"DB_HOST": "localhost"}


def test_strips_double_quoted_values(tmp_env):
    path = tmp_env('SECRET_KEY="my secret value"\n')
    result = parse_env_file(path)
    assert result["SECRET_KEY"] == "my secret value"


def test_strips_single_quoted_values(tmp_env):
    path = tmp_env("TOKEN='abc123'\n")
    result = parse_env_file(path)
    assert result["TOKEN"] == "abc123"


def test_strips_inline_comment(tmp_env):
    path = tmp_env("PORT=8080 # default port\n")
    result = parse_env_file(path)
    assert result["PORT"] == "8080"


def test_empty_value(tmp_env):
    path = tmp_env("EMPTY_VAR=\n")
    result = parse_env_file(path)
    assert result["EMPTY_VAR"] == ""


def test_raises_file_not_found():
    with pytest.raises(FileNotFoundError, match="File not found"):
        parse_env_file("/nonexistent/path/.env")


def test_raises_on_malformed_line(tmp_env):
    path = tmp_env("VALID=ok\nthis is not valid\n")
    with pytest.raises(EnvParseError, match="Malformed line 2"):
        parse_env_file(path)


def test_handles_equals_in_value(tmp_env):
    path = tmp_env("BASE64_KEY=abc==\n")
    result = parse_env_file(path)
    assert result["BASE64_KEY"] == "abc=="
