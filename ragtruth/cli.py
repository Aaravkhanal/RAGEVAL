"""Command-line interface (CLI) for RAGTruth benchmark and evaluation tool."""

from __future__ import annotations
import argparse
import sys
import json
import uvicorn
from ragtruth.dataset.loader import DatasetLoader
from ragtruth.benchmark.suite import BenchmarkSuite
from ragtruth.benchmark.reporter import BenchmarkReporter
from ragtruth.analysis.generate_paper_report import run_and_generate_paper_analysis
from ragtruth.evaluator.evaluator import RAGTruthEvaluator
from ragtruth.core.schemas import Chunk, RetrievedChunk


def main():
    parser = argparse.ArgumentParser(
        prog="ragtruth",
        description="RAGTruth: Research-Grade RAG Faithfulness & Claim Attribution Benchmark",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: run-benchmark
    bench_parser = subparsers.add_parser("benchmark", help="Run ablation benchmark across configurations")
    bench_parser.add_argument("--data-dir", default="data", help="Directory containing corpus and benchmark data")
    bench_parser.add_argument("--output-dir", default="reports", help="Output directory for reports and figures")

    # Subcommand: report
    report_parser = subparsers.add_parser("report", help="Generate paper-style analysis report and figures")
    report_parser.add_argument("--output-dir", default="reports", help="Output directory for paper analysis")

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
        loader = DatasetLoader(args.data_dir)
        corpus = loader.load_corpus()
        items = loader.load_benchmark("all")
        print(f"Loaded {len(corpus)} corpus documents and {len(items)} benchmark items.")
        suite = BenchmarkSuite()
        summaries = suite.run_suite(corpus, items)
        BenchmarkReporter.export(summaries, output_dir=args.output_dir)
        df = BenchmarkReporter.to_dataframe(summaries)
        print("\n=== Benchmark Summary ===")
        print(df.to_string(index=False))

    elif args.command == "report":
        report_path = run_and_generate_paper_analysis(output_dir=args.output_dir)
        print(f"Successfully generated paper analysis at: {report_path}")

    elif args.command == "evaluate":
        evaluator = RAGTruthEvaluator()
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
        uvicorn.run("ragtruth.server.app:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
