"""Run the API and SQLite-backed worker in one service and one persistent runs directory."""

from __future__ import annotations

import os
import json
import signal
import subprocess
import sys
import time


def main() -> int:
    secrets_file = os.environ.get("RAGEVAL_SECRETS_FILE")
    if secrets_file:
        with open(secrets_file, encoding="utf-8") as source:
            credentials = json.load(source)
        for name in ("RAGEVAL_PUBLIC_TOKEN", "RAGEVAL_ADMIN_TOKEN", "RAGEVAL_ALLOWED_HOSTS", "RAGEVAL_CORS_ORIGINS"):
            if name in credentials:
                os.environ[name] = credentials[name]
    if os.environ.get("RAGEVAL_REQUIRE_AUTH") != "1":
        raise SystemExit("Full-service deployment requires RAGEVAL_REQUIRE_AUTH=1")
    if not os.environ.get("RAGEVAL_PUBLIC_TOKEN") or not os.environ.get("RAGEVAL_ADMIN_TOKEN"):
        raise SystemExit("Full-service deployment requires both public and admin tokens")
    port = int(os.environ.get("PORT", "8000"))
    runs = os.environ.get("RAGEVAL_RUNS_DIR", os.path.join(os.getcwd(), "experiments/runs"))
    data = os.environ.get("RAGEVAL_DATA_DIR", os.path.join(os.getcwd(), "data"))
    processes = [
        subprocess.Popen([sys.executable, "-m", "rageval.cli", "worker", "--runs-dir", runs, "--data-dir", data]),
        subprocess.Popen([sys.executable, "-m", "rageval.cli", "serve", "--host", os.environ.get("RAGEVAL_BIND_HOST", "127.0.0.1"), "--port", str(port), "--runs-dir", runs, "--data-dir", data]),
    ]
    stopping = False
    signalled = False

    def stop(_signum: int, _frame: object) -> None:
        nonlocal stopping, signalled
        stopping = True
        signalled = True
        for process in processes:
            if process.poll() is None:
                process.terminate()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while not stopping:
            for process in processes:
                if process.poll() is not None:
                    stopping = True
                    break
            if not stopping:
                time.sleep(1)
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    return 0 if signalled else 1


if __name__ == "__main__":
    raise SystemExit(main())
