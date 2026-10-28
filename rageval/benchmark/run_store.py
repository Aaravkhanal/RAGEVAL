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


def save_run(
    run_dir: str,
    summaries: List[BenchmarkRunSummary],
    extra_manifest: Optional[Dict[str, Any]] = None,
    pipeline_configs: Optional[List[PipelineConfig]] = None,
) -> None:
    os.makedirs(run_dir, exist_ok=True)
    manifest = {
        "run_dir": os.path.abspath(run_dir),
        "environment": environment_snapshot(),
        "configs": [s.config_name for s in summaries],
        **(extra_manifest or {}),
    }
    with open(os.path.join(run_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    with open(os.path.join(run_dir, "summaries.json"), "w", encoding="utf-8") as f:
        json.dump([s.model_dump() for s in summaries], f, indent=2)

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
