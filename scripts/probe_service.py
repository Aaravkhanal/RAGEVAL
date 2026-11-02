"""Probe an authenticated deployment and record concurrent request latency."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import time
from pathlib import Path

import httpx


def percentile(values: list[float], fraction: float) -> float:
    values = sorted(values)
    at = (len(values) - 1) * fraction
    low = int(at)
    return round(values[low] + (values[min(low + 1, len(values) - 1)] - values[low]) * (at - low), 2)


async def probe(
    base_url: str,
    token: str,
    requests: int,
    concurrency: int,
    verify: bool = True,
) -> dict:
    headers = {"X-RAGEVAL-API-TOKEN": token}
    payload = {"question": "What was reported?", "answer": "The source reports 42 [1].", "context_chunks": ["The source reports 42."]}
    async with httpx.AsyncClient(base_url=base_url, timeout=30, verify=verify) as client:
        health = await client.get("/health")
        ready = await client.get("/ready")
        unauthorized = await client.get("/datasets")
        authorized = await client.get("/datasets", headers=headers)
        assert (health.status_code, ready.status_code, unauthorized.status_code, authorized.status_code) == (200, 200, 401, 200)
        gate = asyncio.Semaphore(concurrency)

        async def one() -> tuple[int, float]:
            async with gate:
                start = time.perf_counter()
                response = await client.post("/evaluate/answer", json=payload, headers=headers)
                return response.status_code, (time.perf_counter() - start) * 1000

        results = await asyncio.gather(*(one() for _ in range(requests)))
    codes = [code for code, _ in results]
    latencies = [ms for _, ms in results]
    return {
        "base_url": base_url,
        "requests": requests,
        "concurrency": concurrency,
        "tls_insecure": not verify,
        "health": health.status_code,
        "ready": ready.status_code,
        "unauthorized_read": unauthorized.status_code,
        "authorized_read": authorized.status_code,
        "response_codes": {str(code): codes.count(code) for code in sorted(set(codes))},
        "latency_ms": {
            "p50": percentile(latencies, 0.5),
            "p95": percentile(latencies, 0.95),
            "p99": percentile(latencies, 0.99),
        },
        "note": "End-to-end HTTP timing from the probe client. verify=False skips certificate verification for Caddy local TLS.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--output", type=Path, default=Path("reports/phase8/service_probe.json"))
    parser.add_argument("--insecure", action="store_true", help="Skip TLS certificate verification (Caddy local certs)")
    args = parser.parse_args()
    token = os.environ.get("RAGEVAL_PUBLIC_TOKEN")
    if not token:
        parser.error("Set RAGEVAL_PUBLIC_TOKEN for the authorized probe")
    result = asyncio.run(
        probe(
            args.base_url,
            token,
            args.requests,
            args.concurrency,
            verify=not args.insecure,
        )
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
