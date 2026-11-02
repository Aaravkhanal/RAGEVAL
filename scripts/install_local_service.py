"""Create a per-user launch agent for the local API and worker."""

from __future__ import annotations

import json
import os
import plistlib
import secrets
import sys
from pathlib import Path


def install() -> tuple[Path, Path]:
    repo = Path(__file__).resolve().parents[1]
    python = repo / ".venv/bin/python"
    if not python.exists():
        python = Path(os.environ.get("RAGEVAL_PYTHON") or os.path.realpath(sys.executable))
    support = Path.home() / "Library/Application Support/RAGEVAL"
    logs = Path.home() / "Library/Logs/RAGEVAL"
    agents = Path.home() / "Library/LaunchAgents"
    for directory in (support, logs, agents):
        directory.mkdir(parents=True, exist_ok=True)
    credentials = support / "service.json"
    if not credentials.exists():
        values = {
            "RAGEVAL_PUBLIC_TOKEN": secrets.token_urlsafe(48),
            "RAGEVAL_ADMIN_TOKEN": secrets.token_urlsafe(48),
            "RAGEVAL_ALLOWED_HOSTS": "localhost,127.0.0.1",
            "RAGEVAL_CORS_ORIGINS": "http://127.0.0.1:8000,http://localhost:8000",
        }
        credentials.write_text(json.dumps(values, indent=2) + "\n")
    os.chmod(credentials, 0o600)
    plist = agents / "com.rageval.service.plist"
    data = {
        "Label": "com.rageval.service",
        "ProgramArguments": [str(python), str(repo / "scripts/start_full_service.py")],
        "WorkingDirectory": str(repo),
        "EnvironmentVariables": {
            "RAGEVAL_REQUIRE_AUTH": "1",
            "RAGEVAL_SECRETS_FILE": str(credentials),
            "PORT": "8000",
        },
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": str(logs / "service.log"),
        "StandardErrorPath": str(logs / "service.error.log"),
    }
    with plist.open("wb") as output:
        plistlib.dump(data, output)
    return plist, credentials


if __name__ == "__main__":
    plist, credentials = install()
    print(f"Launch agent: {plist}")
    print(f"Credentials: {credentials} (mode 0600; values not printed)")
