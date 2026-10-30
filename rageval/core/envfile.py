"""Load gitignored .env files. Never overwrite a variable already in the environment."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional


def parse_env_text(text: str) -> dict:
    values = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def load_dotenv_file(path: str | os.PathLike[str], *, overwrite: bool = False) -> int:
    file_path = Path(path)
    if not file_path.is_file():
        return 0
    loaded = 0
    for key, value in parse_env_text(file_path.read_text(encoding="utf-8")).items():
        if not overwrite and key in os.environ and os.environ.get(key):
            continue
        os.environ[key] = value
        loaded += 1
    return loaded


def load_repo_dotenv(*, overwrite: bool = False) -> Optional[str]:
    """Load `.env` from cwd or the package repo root. Returns the path used."""
    here = Path(__file__).resolve()
    candidates: Iterable[Path] = (
        Path.cwd() / ".env",
        here.parents[1] / ".env",  # rageval/.env
        here.parents[2] / ".env",  # repo root
    )
    seen = set()
    used = None
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if load_dotenv_file(resolved, overwrite=overwrite):
            used = str(resolved)
    return used
