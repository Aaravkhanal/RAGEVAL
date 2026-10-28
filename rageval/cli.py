"""Command-line interface (CLI) for RAGeval benchmark and evaluation tool."""

from __future__ import annotations
import argparse
import sys
import json
import uvicorn
from rageval.dataset.loader import DatasetLoader
from rageval.benchmark.suite import BenchmarkSuite
from rageval.benchmark.reporter import BenchmarkReporter
from rageval.analysis.generate_paper_report import run_and_generate_paper_analysis
from rageval.evaluator.evaluator import RAGEvalEvaluator
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

    # Subcommand: report
    report_parser = subparsers.add_parser("report", help="Generate paper-style analysis report and figures")
    report_parser.add_argument("--output-dir", default="reports", help="Output directory for paper analysis")
    report_parser.add_argument("--dataset", default="benchmark_v1", help="Dataset id")
    report_parser.add_argument("--data-dir", default="data", help="Directory containing corpus and benchmark data")

    # Subcommand: evaluate
    eval_parser = subparsers.add_parser("evaluate", help="Perform claim-level evaluation on a specific answer")
    eval_parser.add_argument("--question", required=True, help="Question text")
    eval_parser.add_argument("--answer", required=True, help="Generated answer text")
    eval_parser.add_argument("--context", action="append", required=True, help="Context chunk text (can specify multiple)")

    # Subcommand: serve
    serve_parser = subparsers.add_parser("serve", help="Launch FastAPI web server and interactive dashboard")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host address")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port number")
    serve_parser.add_argument("--reload", action="store_true", help="Enable hot reload")

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

    elif args.command == "report":
        report_path = run_and_generate_paper_analysis(
            output_dir=args.output_dir,
            dataset_id=args.dataset,
            data_dir=args.data_dir,
        )
        print(f"Successfully generated paper analysis at: {report_path}")

    elif args.command == "evaluate":
        evaluator = RAGEvalEvaluator()
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
        uvicorn.run("rageval.server.app:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
