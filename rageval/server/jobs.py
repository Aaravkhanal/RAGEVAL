"""Process-local experiment jobs.

The HTTP request thread never runs BenchmarkSuite. A single background thread
does, writing status.json under experiments/runs/<id>/.
"""

from __future__ import annotations

import glob
import os
import re
import threading
import traceback
from typing import Any, Dict, List, Optional

from rageval.benchmark.experiments import load_experiment, run_experiment
from rageval.benchmark.run_store import create_run_dir, new_run_id, write_run_status
from rageval.server.catalog import data_dir, runs_root

SAFE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")
EXPERIMENTS_DIR = os.path.join("configs", "experiments")
LIGHT_CONFIGS = frozenset({"smoke"})
DEFAULT_HTTP_MAX_ITEMS = 2
MAX_HTTP_ITEMS = 28

_job_lock = threading.Lock()
_busy = False
_busy_lock = threading.Lock()


def _set_busy(value: bool) -> None:
    global _busy
    with _busy_lock:
        _busy = value


def is_busy() -> bool:
    with _busy_lock:
        return _busy


def reset_job_state_for_tests() -> None:
    """Drop the in-process lock. Tests only; not an HTTP API."""
    _set_busy(False)
    if _job_lock.locked():
        _job_lock.release()


def list_named_configs(root: str = EXPERIMENTS_DIR) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in sorted(glob.glob(os.path.join(root, "*.yaml"))):
        name = os.path.splitext(os.path.basename(path))[0]
        heavy = name not in LIGHT_CONFIGS
        rows.append({"name": name, "heavy": heavy})
    return rows


def resolve_config_path(name: str, root: str = EXPERIMENTS_DIR) -> str:
    if not SAFE_NAME.match(name):
        raise ValueError("invalid config name")
    path = os.path.normpath(os.path.join(root, f"{name}.yaml"))
    root_abs = os.path.abspath(root)
    if not os.path.abspath(path).startswith(root_abs + os.sep) and os.path.abspath(path) != root_abs:
        raise ValueError("invalid config name")
    if not os.path.isfile(path):
        raise FileNotFoundError(name)
    return path


def enqueue_experiment(
    config_name: str,
    *,
    max_items: Optional[int] = None,
    allow_heavy: bool = False,
    output_root: Optional[str] = None,
    data_root: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a queued run dir and start a background worker. Returns 202 payload fields."""
    path = resolve_config_path(config_name)
    spec = load_experiment(path)
    if not spec.pipelines:
        raise ValueError(
            f"Experiment {config_name!r} has no pipelines (analysis-only). Use GET /experiments results."
        )
    heavy = config_name not in LIGHT_CONFIGS
    if heavy and not allow_heavy:
        raise PermissionError(
            f"Config {config_name!r} is a heavy NLI/v1 job. Pass allow_heavy=true or run the CLI."
        )
    if max_items is None:
        max_items = DEFAULT_HTTP_MAX_ITEMS
    max_items = int(max_items)
    if max_items < 1 or max_items > MAX_HTTP_ITEMS:
        raise ValueError(f"max_items must be between 1 and {MAX_HTTP_ITEMS}")

    acquired = _job_lock.acquire(blocking=False)
    if not acquired:
        raise RuntimeError("A job is already queued or running")
    _set_busy(True)
    try:
        output_root = output_root or runs_root()
        data_root = data_root or data_dir()
        run_id = new_run_id()
        run_dir = create_run_dir(output_root, run_id=run_id)
        write_run_status(
            run_dir,
            "queued",
            extra={"config": config_name, "max_items": max_items, "allow_heavy": allow_heavy},
        )
    except Exception:
        _set_busy(False)
        _job_lock.release()
        raise

    thread = threading.Thread(
        target=_run_worker,
        kwargs={
            "spec": spec,
            "run_dir": run_dir,
            "data_root": data_root,
            "output_root": output_root,
            "max_items": max_items,
            "config_name": config_name,
        },
        name=f"rageval-job-{run_id}",
        daemon=True,
    )
    thread.start()
    return {
        "id": run_id,
        "status": "queued",
        "poll": f"/experiments/{run_id}",
        "config": config_name,
        "max_items": max_items,
        "heavy": heavy,
    }


def _run_worker(
    *,
    spec,
    run_dir: str,
    data_root: str,
    output_root: str,
    max_items: int,
    config_name: str,
) -> None:
    try:
        write_run_status(run_dir, "running", extra={"config": config_name, "max_items": max_items})
        run_experiment(
            spec,
            data_dir=data_root,
            output_root=output_root,
            max_items=max_items,
            existing_run_dir=run_dir,
        )
        write_run_status(run_dir, "complete", extra={"config": config_name, "max_items": max_items})
    except Exception as exc:
        write_run_status(
            run_dir,
            "failed",
            extra={
                "config": config_name,
                "error": str(exc),
                "error_type": type(exc).__name__,
            },
        )
        traceback.print_exc()
    finally:
        _set_busy(False)
        if _job_lock.locked():
            _job_lock.release()
