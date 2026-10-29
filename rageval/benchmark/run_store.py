"""Non-overwriting experiment run directories and environment snapshots."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import yaml

from rageval.core.config import PipelineConfig
from rageval.core.schemas import BenchmarkRunSummary


def new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}_{uuid.uuid4().hex[:8]}"


def git_commit(cwd: Optional[str] = None) -> Optional[str]:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd or os.getcwd(),
            stderr=subprocess.DEVNULL,
        )
        return out.decode("utf-8").strip()
    except Exception:
        return None


def environment_snapshot() -> Dict[str, Any]:
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "git_commit": git_commit(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


def create_run_dir(output_root: str, run_id: Optional[str] = None) -> str:
    rid = run_id or new_run_id()
    path = os.path.join(output_root, rid)
    if os.path.exists(path):
        raise FileExistsError(f"Run directory already exists: {path}")
    os.makedirs(path, exist_ok=False)
    return path


def _status_path(run_dir: str) -> str:
    return os.path.join(run_dir, "status.json")


def atomic_write_json(path: str, payload: Any) -> None:
    """Write JSON via a sibling temp file so readers never see a truncated body."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.isfile(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def read_run_status(run_dir: str) -> Optional[Dict[str, Any]]:
    path = _status_path(run_dir)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def write_run_status(run_dir: str, state: str, extra: Optional[Dict[str, Any]] = None) -> None:
    payload = {
        "state": state,
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        **(extra or {}),
    }
    atomic_write_json(_status_path(run_dir), payload)


def save_run(
    run_dir: str,
    summaries: List[BenchmarkRunSummary],
    extra_manifest: Optional[Dict[str, Any]] = None,
    pipeline_configs: Optional[List[PipelineConfig]] = None,
    label: Optional[str] = None,
    experiment_id: Optional[str] = None,
) -> None:
    os.makedirs(run_dir, exist_ok=True)
    status = read_run_status(run_dir)
    metrics_json = os.path.join(run_dir, "metrics.json")
    if status and status.get("state") == "complete":
        raise FileExistsError(f"Refusing to overwrite completed run: {run_dir}")
    if os.path.isfile(metrics_json):
        raise FileExistsError(f"Refusing to clobber existing metrics.json in {run_dir}")
    write_run_status(run_dir, "running")
    env = environment_snapshot()
    manifest = {
        "run_dir": os.path.abspath(run_dir),
        "environment": env,
        "configs": [s.config_name for s in summaries],
        "label": label,
        "experiment_id": experiment_id,
        **(extra_manifest or {}),
    }
    atomic_write_json(os.path.join(run_dir, "manifest.json"), manifest)
    atomic_write_json(
        os.path.join(run_dir, "summaries.json"),
        [s.model_dump() for s in summaries],
    )

    pred_path = os.path.join(run_dir, "predictions.jsonl")
    with open(pred_path, "w", encoding="utf-8") as f:
        for summary in summaries:
            for result in summary.results:
                record = result.model_dump()
                record["config_name"] = summary.config_name
                f.write(json.dumps(record) + "\n")

    if pipeline_configs:
        cfg_dir = os.path.join(run_dir, "configs")
        os.makedirs(cfg_dir, exist_ok=True)
        for cfg in pipeline_configs:
            safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in cfg.name)
            with open(os.path.join(cfg_dir, f"{safe_name}.yaml"), "w", encoding="utf-8") as f:
                yaml.safe_dump(cfg.model_dump(), f, sort_keys=False)

    from rageval.metrics.aggregate import write_metrics_bundle

    extra = {
        "label": label or (extra_manifest or {}).get("label"),
        "experiment_id": experiment_id or (extra_manifest or {}).get("experiment_id"),
        "dataset_id": (extra_manifest or {}).get("dataset_id")
        or (summaries[0].dataset_id if summaries else None),
        "dataset_version": (extra_manifest or {}).get("dataset_version")
        or (summaries[0].dataset_version if summaries else None),
        "git_commit": env.get("git_commit"),
        "timestamp_utc": env.get("timestamp_utc"),
        "n_items": (extra_manifest or {}).get("n_items")
        or (summaries[0].total_queries if summaries else 0),
    }
    write_metrics_bundle(run_dir, summaries, independent=False, extra=extra)
    write_run_status(
        run_dir,
        "complete",
        extra={"git_commit": env.get("git_commit"), "n_summaries": len(summaries)},
    )
