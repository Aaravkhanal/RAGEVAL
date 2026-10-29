"""Read-only catalog of datasets and experiment run folders. No suite execution."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from rageval.dataset.loader import DatasetLoader

SECRET_KEY = re.compile(
    r"(secret|token|password|api[_-]?key|authorization|credential|private[_-]?key)",
    re.IGNORECASE,
)
SAFE_ID = re.compile(r"^[A-Za-z0-9_.:-]+$")

COMMITTED_SNAPSHOTS = (
    ("20261028T183042Z_a97ad68f", os.path.join("reports", "phase7", "v1_matrix")),
    ("20261029T165024Z_657c8089", os.path.join("reports", "phase7", "v1_1_matrix")),
)


def runs_root() -> str:
    return os.environ.get("RAGEVAL_RUNS_DIR", os.path.join("experiments", "runs"))


def data_dir() -> str:
    return os.environ.get("RAGEVAL_DATA_DIR", "data")


def snapshots_enabled() -> bool:
    raw = os.environ.get("RAGEVAL_INCLUDE_SNAPSHOTS", "1").strip().lower()
    return raw not in {"0", "false", "no"}


def sanitize(value: Any) -> Any:
    """Drop absolute run_dir and redact secret-like keys."""
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for key, item in value.items():
            if key == "run_dir":
                continue
            if SECRET_KEY.search(str(key)):
                out[key] = "<redacted>"
            else:
                out[key] = sanitize(item)
        return out
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    return value


def _mean(block: dict, key: str) -> Optional[float]:
    value = block.get(key)
    if isinstance(value, dict):
        mean = value.get("mean")
        return float(mean) if mean is not None else None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def table_from_metrics(metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for name, block in (metrics.get("by_config") or {}).items():
        rows.append(
            {
                "config_name": name,
                "mean_faithfulness": _mean(block, "claim_support_rate"),
                "mean_hallucination_rate": _mean(block, "unsupported_claim_rate"),
                "mean_contradiction_rate": _mean(block, "contradiction_rate"),
                "mean_recall_at_5": _mean(block, "recall_at_5"),
                "mean_mrr": _mean(block, "mrr"),
                "abstention_accuracy": block.get("abstention_accuracy"),
                "mean_latency_ms": block.get("mean_latency_ms"),
                "n": block.get("n"),
            }
        )
    return rows


def list_datasets(root: Optional[str] = None) -> List[Dict[str, Any]]:
    base = root or data_dir()
    man_dir = os.path.join(base, "manifests")
    if not os.path.isdir(man_dir):
        return []
    out: List[Dict[str, Any]] = []
    for name in sorted(os.listdir(man_dir)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(man_dir, name)
        with open(path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        out.append(
            {
                "dataset_id": manifest.get("dataset_id") or name[:-5],
                "version": manifest.get("version"),
                "synthetic": manifest.get("synthetic"),
                "license": manifest.get("license"),
                "n_documents": manifest.get("n_documents"),
                "n_items": manifest.get("n_items"),
                "split_policy": manifest.get("split_policy"),
            }
        )
    return out


def _public_item(item) -> Dict[str, Any]:
    test_type = item.test_type.value if hasattr(item.test_type, "value") else item.test_type
    return {
        "id": item.id,
        "domain": item.domain,
        "question": item.question,
        "gold_answer": item.gold_answer,
        "test_type": test_type,
        "scenario_type": item.scenario_type,
        "split": item.split,
        "expected_abstention": item.expected_abstention,
        "answerability": item.answerability,
        "pair_id": item.pair_id,
        "pair_role": item.pair_role,
    }


def get_dataset(dataset_id: str, root: Optional[str] = None, include_items: bool = True) -> Dict[str, Any]:
    if not SAFE_ID.match(dataset_id) or ".." in dataset_id or os.sep in dataset_id:
        raise ValueError("invalid dataset id")
    base = root or data_dir()
    loader = DatasetLoader(base, dataset_id=dataset_id)
    manifest = loader.load_manifest()
    if manifest is None:
        raise FileNotFoundError(dataset_id)
    payload = {
        "dataset_id": manifest.get("dataset_id", dataset_id),
        "version": manifest.get("version"),
        "synthetic": manifest.get("synthetic"),
        "license": manifest.get("license"),
        "n_documents": manifest.get("n_documents"),
        "n_items": manifest.get("n_items"),
        "n_dev": manifest.get("n_dev"),
        "n_test": manifest.get("n_test"),
        "split_policy": manifest.get("split_policy"),
        "notes": manifest.get("notes"),
        "annotator": manifest.get("annotator"),
    }
    if include_items:
        items = loader.load_benchmark("all")
        payload["items"] = [_public_item(item) for item in items]
        payload["n_items_loaded"] = len(items)
    return payload


def _read_json(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def _run_record(run_id: str, path: str, source: str) -> Dict[str, Any]:
    manifest = _read_json(os.path.join(path, "manifest.json")) or {}
    status = _read_json(os.path.join(path, "status.json"))
    metrics = _read_json(os.path.join(path, "metrics.json")) or {}
    has_metrics = bool(metrics)
    state = None
    if status:
        state = status.get("state")
    elif has_metrics:
        state = "complete"
    env = manifest.get("environment") if isinstance(manifest.get("environment"), dict) else {}
    configs = manifest.get("configs")
    if not configs:
        configs = list((metrics.get("by_config") or {}).keys())
    return sanitize(
        {
            "id": run_id,
            "source": source,
            "state": state,
            "label": manifest.get("label", metrics.get("label")),
            "experiment_id": manifest.get("experiment_id", metrics.get("experiment_id")),
            "dataset_id": manifest.get("dataset_id", metrics.get("dataset_id")),
            "dataset_version": manifest.get("dataset_version", metrics.get("dataset_version")),
            "n_items": manifest.get("n_items", metrics.get("n_items")),
            "n_documents": manifest.get("n_documents"),
            "configs": configs,
            "has_metrics": has_metrics,
            "git_commit": env.get("git_commit")
            or manifest.get("git_commit")
            or metrics.get("git_commit"),
        }
    )


def _snapshot_roots() -> List[Tuple[str, str]]:
    if not snapshots_enabled():
        return []
    found: List[Tuple[str, str]] = []
    for run_id, rel in COMMITTED_SNAPSHOTS:
        if os.path.isfile(os.path.join(rel, "metrics.json")):
            found.append((run_id, rel))
    return found


def list_experiments(root: Optional[str] = None) -> List[Dict[str, Any]]:
    base = root or runs_root()
    seen: Dict[str, Dict[str, Any]] = {}
    if os.path.isdir(base):
        for name in sorted(os.listdir(base)):
            path = os.path.join(base, name)
            if not os.path.isdir(path):
                continue
            if not (
                os.path.isfile(os.path.join(path, "metrics.json"))
                or os.path.isfile(os.path.join(path, "manifest.json"))
                or os.path.isfile(os.path.join(path, "status.json"))
            ):
                continue
            seen[name] = _run_record(name, path, source="runs")
    for run_id, rel in _snapshot_roots():
        snap = _run_record(run_id, rel, source="committed_snapshot")
        if run_id not in seen:
            seen[run_id] = snap
        elif not seen[run_id].get("has_metrics") and snap.get("has_metrics"):
            seen[run_id]["has_metrics"] = True
            seen[run_id]["results_source"] = "committed_snapshot"
            if not seen[run_id].get("configs"):
                seen[run_id]["configs"] = snap.get("configs")
    return [seen[key] for key in sorted(seen)]


def resolve_experiment_dir(
    run_id: str,
    root: Optional[str] = None,
    *,
    require_metrics: bool = False,
) -> Tuple[str, str]:
    if not SAFE_ID.match(run_id) or ".." in run_id or os.sep in run_id:
        raise ValueError("invalid experiment id")
    base = root or runs_root()
    local = os.path.join(base, run_id)
    snapshot = None
    for sid, rel in _snapshot_roots():
        if sid == run_id:
            snapshot = rel
            break
    local_metrics = os.path.isdir(local) and os.path.isfile(os.path.join(local, "metrics.json"))
    snapshot_metrics = snapshot is not None and os.path.isfile(os.path.join(snapshot, "metrics.json"))
    if require_metrics:
        if local_metrics:
            return local, "runs"
        if snapshot_metrics:
            return snapshot, "committed_snapshot"
        raise FileNotFoundError(run_id)
    if os.path.isdir(local):
        return local, "runs"
    if snapshot is not None:
        return snapshot, "committed_snapshot"
    raise FileNotFoundError(run_id)


def get_experiment(run_id: str, root: Optional[str] = None) -> Dict[str, Any]:
    path, source = resolve_experiment_dir(run_id, root)
    record = _run_record(run_id, path, source)
    manifest = sanitize(_read_json(os.path.join(path, "manifest.json")) or {})
    status = sanitize(_read_json(os.path.join(path, "status.json")) or {})
    record["manifest"] = manifest
    record["status"] = status or None
    if source == "runs" and not record.get("has_metrics"):
        try:
            snap_path, snap_source = resolve_experiment_dir(run_id, root, require_metrics=True)
        except FileNotFoundError:
            snap_path = None
            snap_source = None
        if snap_source == "committed_snapshot" and snap_path:
            record["has_metrics"] = True
            record["results_source"] = snap_source
    return record


def get_experiment_results(run_id: str, root: Optional[str] = None) -> Dict[str, Any]:
    path, source = resolve_experiment_dir(run_id, root, require_metrics=True)
    metrics = _read_json(os.path.join(path, "metrics.json"))
    if metrics is None:
        raise FileNotFoundError("metrics.json")
    return {
        "id": run_id,
        "source": source,
        "metrics": metrics,
        "table": table_from_metrics(metrics),
    }
