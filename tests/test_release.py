"""Release checks: version, license, reports match the recorded run, no secrets."""

import json
import re
from pathlib import Path

import rageval
from rageval.analysis.findings import assert_findings_text_allowed, recall_relative_lift_pct
from rageval.benchmark.experiments import load_experiment
from rageval.benchmark.reporter import BenchmarkReporter
from rageval.core.config import pipeline_config_from_yaml

ROOT = Path(__file__).resolve().parents[1]
SECRET_VALUE = re.compile(
    r"(sk-[A-Za-z0-9]{10,}|hf_[A-Za-z0-9]{10,}|AKIA[0-9A-Z]{16}|BEGIN (RSA |OPENSSH )?PRIVATE KEY)"
)


def test_version_is_release():
    assert rageval.__version__ == "0.2.1"
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(r'(?m)^version = "0.2.1"$', pyproject)
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [0.2.1]" in changelog
    assert "## [0.2.0]" in changelog
    assert "Keep a Changelog" in changelog
    assert "20261028T183042Z_a97ad68f" in changelog
    assert "twine upload" in changelog
    assert "POST /experiments" in changelog
    from rageval.server.app import app

    assert app.version == "0.2.1"


def test_license_files_exist():
    assert (ROOT / "LICENSE").is_file()
    assert "MIT License" in (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert (ROOT / "data" / "LICENSE.md").is_file()


def test_hashed_lockfiles():
    fast = (ROOT / "requirements-lock-fast.txt").read_text(encoding="utf-8")
    all_lock = (ROOT / "requirements-lock-all.txt").read_text(encoding="utf-8")
    assert "--hash=sha256:" in fast
    assert "--hash=sha256:" in all_lock
    assert "torch==" not in fast
    assert "faiss-cpu==" not in fast
    assert "torch==" in all_lock and "+cpu" in all_lock
    assert "faiss-cpu==" in all_lock
    assert "download.pytorch.org/whl/cpu" in all_lock
    assert (ROOT / "Dockerfile").is_file()
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "requirements-lock-all.txt" in dockerfile
    assert '"rageval", "serve"' in dockerfile
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "requirements-lock-fast.txt" in ci
    assert "--require-hashes" in ci
    assert (ROOT / "scripts" / "compile_locks.sh").is_file()


def test_hf_workflow_is_strict():
    nightly = (ROOT / ".github" / "workflows" / "nightly.yml").read_text(encoding="utf-8")
    assert "continue-on-error:" not in nightly
    assert "actions/cache@v4" in nightly
    assert ".cache/huggingface" in nightly
    assert "timeout-minutes: 90" in nightly
    assert 'python-version: "3.12"' in nightly
    assert "requirements-lock-all.txt" in nightly
    assert "pytest -m hf" in nightly
    assert "workflow_dispatch" in nightly
    assert "0 6 * * 1" in nightly
    repro = (ROOT / "docs" / "REPRODUCIBILITY.md").read_text(encoding="utf-8")
    assert "https://github.com/Aaravkhanal/RAGEVAL/actions/runs/" in repro
    assert "pending this phase" not in repro


def test_smoke_experiment_yaml():
    spec = load_experiment(str(ROOT / "configs" / "experiments" / "smoke.yaml"))
    assert spec.experiment_id == "smoke"
    assert spec.dataset_id == "smoke_v1"
    assert spec.pipelines
    assert spec.pipelines[0].retriever.method == "sparse"
    assert spec.pipelines[0].evaluator.method == "heuristic"
    cfg = pipeline_config_from_yaml(str(ROOT / "configs" / "smoke_sparse_heuristic.yaml"))
    assert cfg.reranker.enabled is False


def test_reports_match_recorded_metrics():
    metrics = BenchmarkReporter.load_metrics(str(ROOT / "reports" / "phase7" / "v1_matrix" / "metrics.json"))
    assert metrics["n_items"] == 24
    assert metrics["dataset_id"] == "benchmark_v1"
    assert metrics.get("overall_score") is None
    lift = recall_relative_lift_pct(metrics, "Dense_Chunk256_Baseline", "Hybrid_RRF_Reranked")
    assert lift == 0.0
    findings = (ROOT / "reports" / "20261028T183042Z_a97ad68f" / "FINDINGS.md").read_text(encoding="utf-8")
    paper = (ROOT / "reports" / "paper.tex").read_text(encoding="utf-8")
    assert "16.4%" not in findings
    assert "16.4%" not in paper
    assert "0.8333" in findings and "0.8333" in paper
    assert "0.4375" in findings and "0.4375" in paper
    assert_findings_text_allowed(findings, metrics)


def test_v11_companion_snapshot_does_not_replace_published_tables():
    v11 = BenchmarkReporter.load_metrics(str(ROOT / "reports" / "phase7" / "v1_1_matrix" / "metrics.json"))
    v10 = BenchmarkReporter.load_metrics(str(ROOT / "reports" / "phase7" / "v1_matrix" / "metrics.json"))
    assert v10["n_items"] == 24
    assert v10["dataset_version"] == "1.0.0"
    assert v11["n_items"] == 28
    assert v11["dataset_version"] == "1.1.0"
    assert v11.get("n_documents") == 18
    assert v11.get("overall_score") is None
    assert v11["by_config"]["Dense_Chunk256_Baseline"]["claim_support_rate"]["mean"] == 0.3929
    assert v10["by_config"]["Dense_Chunk256_Baseline"]["claim_support_rate"]["mean"] == 0.4375
    findings = (ROOT / "reports" / "20261029T165024Z_657c8089" / "FINDINGS.md").read_text(encoding="utf-8")
    paper = (ROOT / "reports" / "paper.tex").read_text(encoding="utf-8")
    assert "16.4%" not in findings
    assert "unscored" not in findings
    assert "0.8571" in findings
    assert "20261028T183042Z_a97ad68f" in findings
    assert "0.4375" in paper
    assert_findings_text_allowed(findings, v11)


def test_cli_benchmark_reporter_import_is_module_level():
    src = (ROOT / "rageval" / "cli.py").read_text(encoding="utf-8")
    matches = [
        line for line in src.splitlines() if "from rageval.benchmark.reporter import BenchmarkReporter" in line
    ]
    assert len(matches) == 1
    assert not matches[0].startswith(" ")


def test_tracked_text_has_no_live_credentials():
    skip_dirs = {".git", ".venv", "venv", "env", "__pycache__", "experiments", "rageval.egg-info", "ragtruth.egg-info"}
    skip_suffix = {".png", ".jpg", ".pyc", ".so", ".bin", ".pt"}
    hits = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in skip_dirs for part in path.parts):
            continue
        if path.suffix.lower() in skip_suffix:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if SECRET_VALUE.search(text):
            hits.append(str(path.relative_to(ROOT)))
    assert hits == []
