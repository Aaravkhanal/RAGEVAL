"""Durable experiment queue shared by API and worker processes."""
from __future__ import annotations

import glob
import os
import re
import sqlite3
import threading
import time
import traceback
from contextlib import closing
from typing import Any, Dict, List, Optional

from rageval.benchmark.experiments import load_experiment, run_experiment
from rageval.benchmark.run_store import create_run_dir, new_run_id, read_run_status, write_run_status
from rageval.server.catalog import data_dir, runs_root
from rageval.core.assets import resolve_asset

SAFE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")
EXPERIMENTS_DIR = resolve_asset(os.path.join("configs", "experiments"))
LIGHT_CONFIGS = frozenset({"smoke"})
DEFAULT_HTTP_MAX_ITEMS = 2
MAX_HTTP_ITEMS = 32
LEASE_SECONDS = 30.0


def _connect(root: Optional[str] = None) -> sqlite3.Connection:
    root = root or runs_root()
    os.makedirs(root, exist_ok=True)
    conn = sqlite3.connect(os.path.join(root, "jobs.sqlite3"), timeout=10)
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, config TEXT NOT NULL, "
                 "max_items INTEGER NOT NULL, state TEXT NOT NULL, "
                 "lease_until REAL NOT NULL DEFAULT 0, updated REAL NOT NULL)")
    conn.commit()
    return conn


def is_busy() -> bool:
    if not os.path.isdir(runs_root()):
        return False
    try:
        with closing(_connect()) as conn, conn:
            return conn.execute("SELECT 1 FROM jobs WHERE state='queued' OR "
                                "(state='running' AND lease_until>?) LIMIT 1",
                                (time.time(),)).fetchone() is not None
    except (OSError, sqlite3.Error):
        return False


def reset_job_state_for_tests() -> None:
    """Tests isolate the queue through RAGEVAL_RUNS_DIR."""


def list_named_configs(root: Optional[str] = None) -> List[Dict[str, Any]]:
    root = resolve_asset(root or EXPERIMENTS_DIR)
    names = [os.path.splitext(os.path.basename(p))[0]
             for p in sorted(glob.glob(os.path.join(root, "*.yaml")))]
    if os.environ.get("RAGEVAL_LIGHT_ONLY", "0") == "1":
        names = [name for name in names if name in LIGHT_CONFIGS]
    return [{"name": name, "heavy": name not in LIGHT_CONFIGS} for name in names]


def resolve_config_path(name: str, root: Optional[str] = None) -> str:
    root = resolve_asset(root or EXPERIMENTS_DIR)
    if not SAFE_NAME.fullmatch(name):
        raise ValueError("invalid config name")
    path = os.path.join(root, f"{name}.yaml")
    if not os.path.isfile(path):
        raise FileNotFoundError(name)
    return path


def enqueue_experiment(config_name: str, *, max_items: Optional[int] = None,
                       allow_heavy: bool = False, output_root: Optional[str] = None,
                       data_root: Optional[str] = None) -> Dict[str, Any]:
    """Validate and durably queue a job; a separate worker executes it."""
    spec = load_experiment(resolve_config_path(config_name))
    if spec.opt_in or any(p.opt_in for p in spec.pipelines):
        raise PermissionError("HTTP jobs cannot run opt-in LLM configs. Use the CLI with --allow-opt-in.")
    if not spec.pipelines:
        raise ValueError(f"Experiment {config_name!r} has no pipelines (analysis-only). Use GET /experiments results.")
    heavy = config_name not in LIGHT_CONFIGS
    if heavy and os.environ.get("RAGEVAL_LIGHT_ONLY", "0") == "1":
        raise PermissionError("This deployment accepts only lightweight smoke jobs")
    if heavy and not allow_heavy:
        raise PermissionError(f"Config {config_name!r} is a heavy job. Pass allow_heavy=true or run the CLI.")
    max_items = DEFAULT_HTTP_MAX_ITEMS if max_items is None else int(max_items)
    if not 1 <= max_items <= MAX_HTTP_ITEMS:
        raise ValueError(f"max_items must be between 1 and {MAX_HTTP_ITEMS}")
    output_root = output_root or runs_root()
    if not os.path.isdir(data_root or data_dir()):
        raise FileNotFoundError(data_root or data_dir())
    with closing(_connect(output_root)) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        if conn.execute("SELECT 1 FROM jobs WHERE state='queued' OR "
                        "(state='running' AND lease_until>?) LIMIT 1",
                        (time.time(),)).fetchone():
            raise RuntimeError("A job is already queued or running")
        run_id = new_run_id()
        run_dir = create_run_dir(output_root, run_id=run_id)
        write_run_status(run_dir, "queued", extra={"config": config_name, "max_items": max_items})
        conn.execute("INSERT INTO jobs(id,config,max_items,state,updated) VALUES (?,?,?,?,?)",
                     (run_id, config_name, max_items, "queued", time.time()))
    return {"id": run_id, "status": "queued", "poll": f"/experiments/{run_id}",
            "config": config_name, "max_items": max_items, "heavy": heavy}


def run_next_job(output_root: Optional[str] = None, data_root: Optional[str] = None) -> bool:
    """Claim and execute one job; an expired lease makes a crashed job retryable."""
    output_root, data_root = output_root or runs_root(), data_root or data_dir()
    with closing(_connect(output_root)) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        now = time.time()
        if conn.execute("SELECT 1 FROM jobs WHERE state='running' AND lease_until>? LIMIT 1",
                        (now,)).fetchone():
            return False
        row = conn.execute("SELECT id,config,max_items FROM jobs WHERE state='queued' OR "
                           "(state='running' AND lease_until<=?) ORDER BY updated LIMIT 1",
                           (now,)).fetchone()
        if row is None:
            return False
        run_id, config_name, max_items = row
        conn.execute("UPDATE jobs SET state='running',lease_until=?,updated=? WHERE id=?",
                     (now + LEASE_SECONDS, now, run_id))
    run_dir = os.path.join(output_root, run_id)
    if (read_run_status(run_dir) or {}).get("state") == "complete":
        with closing(_connect(output_root)) as conn, conn:
            conn.execute("UPDATE jobs SET state='complete',lease_until=0,updated=? WHERE id=?",
                         (time.time(), run_id))
        return True
    stopped = threading.Event()

    def heartbeat() -> None:
        while not stopped.wait(LEASE_SECONDS / 3):
            with closing(_connect(output_root)) as conn, conn:
                conn.execute("UPDATE jobs SET lease_until=?,updated=? WHERE id=? AND state='running'",
                             (time.time() + LEASE_SECONDS, time.time(), run_id))

    pulse = threading.Thread(target=heartbeat, daemon=True)
    pulse.start()
    state = "complete"
    try:
        write_run_status(run_dir, "running", extra={"config": config_name, "max_items": max_items})
        run_experiment(load_experiment(resolve_config_path(config_name)), data_dir=data_root,
                       output_root=output_root, max_items=max_items, existing_run_dir=run_dir)
        write_run_status(run_dir, "complete", extra={"config": config_name, "max_items": max_items})
        if os.environ.get("RAGEVAL_SUPABASE_URL"):
            from rageval.server.workspace import save
            from rageval.server.catalog import get_experiment_results
            save('run', get_experiment_results(run_id, output_root))
    except Exception as exc:
        state = "failed"
        write_run_status(run_dir, "failed", extra={"config": config_name, "error": str(exc),
                                                    "error_type": type(exc).__name__})
        traceback.print_exc()
    finally:
        stopped.set()
        pulse.join(timeout=1)
        with closing(_connect(output_root)) as conn, conn:
            conn.execute("UPDATE jobs SET state=?,lease_until=0,updated=? WHERE id=?",
                         (state, time.time(), run_id))
    return True


def worker_forever(output_root: Optional[str] = None, data_root: Optional[str] = None) -> None:
    while True:
        if not run_next_job(output_root, data_root):
            time.sleep(1)
