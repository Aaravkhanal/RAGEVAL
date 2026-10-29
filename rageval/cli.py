"""Command-line interface (CLI) for RAGeval benchmark and evaluation tool."""

from __future__ import annotations
import argparse
import os
import sys
import json
from rageval.dataset.loader import DatasetLoader
from rageval.benchmark.suite import BenchmarkSuite
from rageval.benchmark.reporter import BenchmarkReporter
from rageval.analysis.generate_paper_report import run_and_generate_paper_analysis
from rageval.evaluator.evaluator import RAGEvalEvaluator
from rageval.core.config import EvaluatorConfig
from rageval.core.schemas import Chunk, RetrievedChunk


def main():
    parser = argparse.ArgumentParser(
        prog="rageval",
        description="RAGeval: Research-Grade RAG Faithfulness & Claim Attribution Benchmark",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: run-benchmark
    bench_parser = subparsers.add_parser("benchmark", help="Run ablation benchmark across configurations")
    bench_parser.add_argument("--data-dir", default="data", help="Directory containing corpus and benchmark data")
    bench_parser.add_argument(
        "--dataset",
        default="benchmark_v1",
        help="Dataset id (smoke_v1 or benchmark_v1)",
    )
    bench_parser.add_argument(
        "--split",
        default="all",
        help="Item split: all, standard, adversarial, dev, or test",
    )
    bench_parser.add_argument(
        "--output-dir",
        default="experiments/runs",
        help="Parent directory for unique run folders (never overwritten)",
    )
    bench_parser.add_argument(
        "--config",
        action="append",
        default=None,
        help="Pipeline YAML (repeatable). Default is the 6-config ablation matrix.",
    )

    validate_parser = subparsers.add_parser("validate", help="Validate corpus/item integrity for a dataset")
    validate_parser.add_argument("--data-dir", default="data")
    validate_parser.add_argument("--dataset", default="benchmark_v1")
    validate_parser.add_argument("--split", default="all")

    ver_parser = subparsers.add_parser(
        "verifier-eval",
        help="Score a verifier against data/gold/verifier_eval_v1.json (RQ2)",
    )
    ver_parser.add_argument("--gold", default="data/gold/verifier_eval_v1.json")
    ver_parser.add_argument("--method", default="nli", choices=["nli", "heuristic"])
    ver_parser.add_argument("--output", default="reports/verifier_eval_v1.md")

    # Subcommand: report
    report_parser = subparsers.add_parser("report", help="Write tables from metrics.json (does not re-run the suite)")
    report_parser.add_argument("--output-dir", default="reports", help="Output directory for paper analysis")
    report_parser.add_argument("--dataset", default="benchmark_v1", help="Dataset id")
    report_parser.add_argument("--data-dir", default="data", help="Directory containing corpus and benchmark data")
    report_parser.add_argument("--metrics", default=None, help="Path to metrics.json")
    report_parser.add_argument("--run-dir", default=None, help="Run directory containing metrics.json")

    exp_parser = subparsers.add_parser("experiment", help="Run a named Phase 7 experiment YAML")
    exp_parser.add_argument("--config", required=True, help="configs/experiments/*.yaml")
    exp_parser.add_argument("--data-dir", default="data")
    exp_parser.add_argument("--output-dir", default="experiments/runs")
    exp_parser.add_argument("--max-items", type=int, default=None, help="Optional cap for dry runs")

    findings_parser = subparsers.add_parser("findings", help="Write FINDINGS.md from metrics.json")
    findings_parser.add_argument("--metrics", default="reports/phase7/v1_matrix/metrics.json")
    findings_parser.add_argument("--output-dir", default="reports/20261028T183042Z_a97ad68f")
    findings_parser.add_argument("--run-id", default="20261028T183042Z_a97ad68f")
    findings_parser.add_argument("--case-studies", default="reports/20261028T183042Z_a97ad68f/case_studies.json")

    # Subcommand: evaluate
    eval_parser = subparsers.add_parser("evaluate", help="Perform claim-level evaluation on a specific answer")
    eval_parser.add_argument("--question", required=True, help="Question text")
    eval_parser.add_argument("--answer", required=True, help="Generated answer text")
    eval_parser.add_argument("--context", action="append", required=True, help="Context chunk text (can specify multiple)")
    eval_parser.add_argument("--method", default="nli", choices=["nli", "heuristic"], help="Verifier method")

    # Subcommand: serve
    serve_parser = subparsers.add_parser("serve", help="Launch FastAPI web server and interactive dashboard")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host address")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port number")
    serve_parser.add_argument("--reload", action="store_true", help="Enable hot reload")
    serve_parser.add_argument("--runs-dir", default="experiments/runs", help="Experiment run root for GET /experiments")
    serve_parser.add_argument("--data-dir", default="data", help="Dataset root for GET /datasets")

    args = parser.parse_args()

    if args.command == "benchmark":
        from rageval.benchmark.run_store import create_run_dir, save_run

        loader = DatasetLoader(args.data_dir, dataset_id=args.dataset)
        corpus = loader.load_corpus()
        items = loader.load_benchmark(args.split)
        manifest = loader.load_manifest() or {}
        dataset_version = manifest.get("version")
        print(
            f"Loaded {len(corpus)} corpus documents and {len(items)} benchmark items "
            f"(dataset={args.dataset}, split={args.split})."
        )
        if args.config:
            from rageval.core.config import pipeline_config_from_yaml

            suite = BenchmarkSuite([pipeline_config_from_yaml(path) for path in args.config])
        else:
            suite = BenchmarkSuite()
        summaries = suite.run_suite(
            corpus,
            items,
            dataset_id=args.dataset,
            dataset_version=dataset_version,
        )
        run_dir = create_run_dir(args.output_dir)
        save_run(
            run_dir,
            summaries,
            extra_manifest={
                "data_dir": args.data_dir,
                "dataset_id": args.dataset,
                "dataset_version": dataset_version,
                "split": args.split,
                "n_documents": len(corpus),
                "n_items": len(items),
            },
            pipeline_configs=suite.configs,
        )
        BenchmarkReporter.export(summaries, output_dir=run_dir)
        df = BenchmarkReporter.to_dataframe(summaries)
        print(f"\nRun directory: {run_dir}")
        print("\n=== Benchmark Summary ===")
        print(df.to_string(index=False))

    elif args.command == "validate":
        from rageval.dataset.validator import validate_benchmark_integrity

        loader = DatasetLoader(args.data_dir, dataset_id=args.dataset)
        corpus = loader.load_corpus()
        items = loader.load_benchmark(args.split)
        licensed = args.dataset != "smoke_v1"
        report = validate_benchmark_integrity(
            corpus,
            items,
            require_license=licensed,
            require_verbatim_spans=licensed,
        )
        print(json.dumps(report, indent=2))
        if not report["valid"]:
            sys.exit(1)

    elif args.command == "verifier-eval":
        from rageval.evaluator.gold_eval import evaluate_verifier_on_gold, write_report

        result = evaluate_verifier_on_gold(args.gold, method=args.method)
        path = write_report(result, args.output)
        print(f"Wrote {path} (macro-F1={result['macro_f1']}, n={result['n']}, method={result['method']})")
        print(f"Failures: {len(result['failures'])}/{result['n']}")

    elif args.command == "experiment":
        from rageval.benchmark.experiments import load_experiment, run_experiment

        spec = load_experiment(args.config)
        run_dir = run_experiment(
            spec,
            data_dir=args.data_dir,
            output_root=args.output_dir,
            max_items=args.max_items,
        )
        print(f"Experiment {spec.experiment_id} ({spec.label}) wrote {run_dir}")

    elif args.command == "report":
        report_path = run_and_generate_paper_analysis(
            output_dir=args.output_dir,
            dataset_id=args.dataset,
            data_dir=args.data_dir,
            metrics_path=args.metrics,
            run_dir=args.run_dir,
        )
        print(f"Successfully generated paper analysis at: {report_path}")

    elif args.command == "findings":
        from rageval.analysis.findings import load_case_studies, write_findings
        from rageval.analysis.paper_plots import generate_figures_from_metrics
        from rageval.benchmark.reporter import BenchmarkReporter

        metrics = BenchmarkReporter.load_metrics(args.metrics)
        cases = load_case_studies(args.case_studies) if args.case_studies else []
        path = write_findings(
            metrics,
            args.output_dir,
            run_id=args.run_id,
            case_studies=cases,
        )
        fig_dir = os.path.join(args.output_dir, "figures")
        generate_figures_from_metrics(metrics, fig_dir)
        print(f"Wrote {path}")

    elif args.command == "evaluate":
        evaluator = RAGEvalEvaluator(EvaluatorConfig(method=args.method))
        retrieved_chunks = [
            RetrievedChunk(
                chunk=Chunk(
                    id=f"cli_chk_{i}",
                    doc_id=f"cli_doc_{i}",
                    text=c,
                    chunk_index=i-1,
                    token_count=len(c.split()),
                    start_char=0,
                    end_char=len(c),
                ),
                score=1.0,
                rank=i,
                retrieval_method="cli_input",
            )
            for i, c in enumerate(args.context, start=1)
        ]
        result = evaluator.evaluate_query(
            question=args.question,
            generated_answer=args.answer,
            retrieved_chunks=retrieved_chunks,
        )
        print(json.dumps(result.model_dump(), indent=2))

    elif args.command == "serve":
        import uvicorn

        os.environ["RAGEVAL_RUNS_DIR"] = args.runs_dir
        os.environ["RAGEVAL_DATA_DIR"] = args.data_dir
        uvicorn.run("rageval.server.app:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
