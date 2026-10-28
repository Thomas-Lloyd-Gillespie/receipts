"""Find the Anthropic API key without ever printing it."""

from __future__ import annotations

import os
import pathlib

VAR = "ANTHROPIC_API_KEY"


def load_key(env_file: str | None = None) -> str:
    if os.environ.get(VAR):
        return os.environ[VAR]
    path = pathlib.Path(env_file) if env_file else pathlib.Path(__file__).parents[1] / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            if line.startswith(f"{VAR}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(f"{VAR} is not set (looked in the environment and {path})")
