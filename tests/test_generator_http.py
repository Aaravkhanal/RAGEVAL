"""OpenAI-like HTTP generator: mocked transport, env keys, no gold leakage."""

from __future__ import annotations

import json

import httpx
import pytest
from pydantic import ValidationError

from rageval.core.config import GeneratorConfig
from rageval.core.schemas import BenchmarkItem, Chunk, RetrievedChunk, TestType
from rageval.metrics.system import estimated_cost_usd
from rageval.pipeline.generator import (
    OPENAI_DEFAULT_BASE_URL,
    OLLAMA_DEFAULT_BASE_URL,
    OpenAILikeGenerator,
    get_generator,
    resolve_api_key,
)


def _chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(
            id="c1",
            doc_id="d1",
            text="ApexCloud non-GAAP gross margin expanded to 78.2% in Q3 2024.",
            chunk_index=0,
            token_count=10,
            start_char=0,
            end_char=60,
        ),
        score=1.0,
        rank=1,
    )


def _poisoned_item() -> BenchmarkItem:
    return BenchmarkItem(
        id="leak",
        question="What is monthly churn?",
        gold_answer="LEAKED_GOLD_ANSWER_TOKEN",
        test_type=TestType.UNANSWERABLE,
        expected_abstention=True,
        scenario_type="unanswerable",
    )


def _client_factory(handler):
    transport = httpx.MockTransport(handler)

    def factory(timeout: float):
        return httpx.Client(transport=transport, timeout=timeout)

    return factory


def test_openai_missing_key_hard_fails(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("RAGEVAL_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        get_generator(GeneratorConfig(backend="openai", model_name="gpt-4o-mini"))


def test_openai_reads_env_key_not_yaml(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    gen = get_generator(
        GeneratorConfig(backend="openai", model_name="gpt-4o-mini", base_url=OPENAI_DEFAULT_BASE_URL)
    )
    assert isinstance(gen, OpenAILikeGenerator)
    assert gen.api_key == "test-openai-key"
    assert gen.base_url == OPENAI_DEFAULT_BASE_URL


def test_ollama_default_base_url_allows_empty_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("RAGEVAL_API_KEY", raising=False)
    gen = get_generator(GeneratorConfig(backend="ollama", model_name="llama3"))
    assert isinstance(gen, OpenAILikeGenerator)
    assert gen.base_url == OLLAMA_DEFAULT_BASE_URL
    assert gen.api_key == ""


def test_generator_config_forbids_api_key_field():
    with pytest.raises(ValidationError):
        GeneratorConfig(backend="openai", api_key="should-not-be-here")


def test_openai_http_success_blinds_and_passes_usage(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers.get("authorization")
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Gross margin expanded to 78.2% [1]."}}],
                "usage": {"prompt_tokens": 41, "completion_tokens": 8},
            },
        )

    monkeypatch.setattr("rageval.pipeline.generator._httpx_client", _client_factory(handler))
    gen = get_generator(
        GeneratorConfig(
            backend="openai",
            model_name="gpt-4o-mini",
            temperature=0.0,
            max_tokens=128,
        )
    )
    answer, prompt_tokens, completion_tokens = gen.generate(
        "What was ApexCloud gross margin?",
        [_chunk()],
        item=_poisoned_item(),
    )
    assert answer == "Gross margin expanded to 78.2% [1]."
    assert prompt_tokens == 41
    assert completion_tokens == 8
    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["authorization"] == "Bearer test-openai-key"
    user = captured["body"]["messages"][1]["content"]
    assert "78.2%" in user
    assert "What was ApexCloud gross margin?" in user
    assert "LEAKED_GOLD_ANSWER_TOKEN" not in user
    assert "test_type" not in user
    assert "UNANSWERABLE" not in user
    assert "expected_abstention" not in user
    assert captured["body"]["temperature"] == 0.0
    assert captured["body"]["max_tokens"] == 128
    cost, source = estimated_cost_usd(prompt_tokens, completion_tokens, None, None, None)
    assert cost is None and source is None
    cost, source = estimated_cost_usd(prompt_tokens, completion_tokens, 1.0, 2.0, "vendor-list")
    assert source == "vendor-list"
    assert cost == pytest.approx((41 * 1.0 + 8 * 2.0) / 1_000_000.0)


def test_openai_http_error_raises_not_answer(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="upstream exploded")

    monkeypatch.setattr("rageval.pipeline.generator._httpx_client", _client_factory(handler))
    gen = get_generator(GeneratorConfig(backend="openai", model_name="gpt-4o-mini"))
    with pytest.raises(RuntimeError, match="LLM HTTP 500") as excinfo:
        gen.generate("Q", [_chunk()], item=_poisoned_item())
    assert "Error contacting LLM endpoint" not in str(excinfo.value)


def test_openai_connect_error_raises(monkeypatch):
    monkeypatch.setenv("RAGEVAL_API_KEY", "test-rageval-key")

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    monkeypatch.setattr("rageval.pipeline.generator._httpx_client", _client_factory(handler))
    gen = get_generator(GeneratorConfig(backend="openai", model_name="gpt-4o-mini"))
    with pytest.raises(RuntimeError, match="LLM HTTP request failed"):
        gen.generate("Q", [_chunk()])


def test_resolve_api_key_prefers_named_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "openai-default")
    monkeypatch.setenv("MY_CUSTOM_KEY", "custom-value")
    assert resolve_api_key("openai", "MY_CUSTOM_KEY") == "custom-value"
