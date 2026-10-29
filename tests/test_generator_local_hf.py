"""local_hf generator: stubbed pipeline, blinding, no mock fallback."""

from __future__ import annotations

import pytest

from rageval.core.config import GeneratorConfig, pipeline_config_from_yaml
from rageval.core.schemas import BenchmarkItem, Chunk, RetrievedChunk, TestType
from rageval.pipeline.generator import LocalHfGenerator, get_generator


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


def test_get_generator_local_hf_is_lazy():
    gen = get_generator(
        GeneratorConfig(backend="local_hf", model_name="sshleifer/tiny-gpt2", max_tokens=32)
    )
    assert isinstance(gen, LocalHfGenerator)
    assert gen._pipeline is None


def test_local_hf_stub_blinds_and_returns_text(monkeypatch):
    captured = {}

    class StubPipe:
        def __call__(self, prompt, **kwargs):
            captured["prompt"] = prompt
            captured["kwargs"] = kwargs
            return [{"generated_text": "Gross margin expanded to 78.2% [1]."}]

    monkeypatch.setattr(LocalHfGenerator, "_build_pipeline", lambda self: StubPipe())
    gen = LocalHfGenerator(model_name="stub-model", temperature=0.0, max_tokens=64)
    answer, prompt_tokens, completion_tokens = gen.generate(
        "What was ApexCloud gross margin?",
        [_chunk()],
        item=_poisoned_item(),
    )
    assert answer == "Gross margin expanded to 78.2% [1]."
    assert prompt_tokens > 0
    assert completion_tokens > 0
    prompt = captured["prompt"]
    assert "78.2%" in prompt
    assert "What was ApexCloud gross margin?" in prompt
    assert "LEAKED_GOLD_ANSWER_TOKEN" not in prompt
    assert "test_type" not in prompt
    assert "UNANSWERABLE" not in prompt
    assert captured["kwargs"]["do_sample"] is False
    assert captured["kwargs"]["max_new_tokens"] == 64


def test_local_hf_missing_transformers(monkeypatch):
    def boom():
        raise ImportError("No module named 'transformers'")

    monkeypatch.setattr("rageval.pipeline.generator._import_transformers_pipeline", boom)
    gen = LocalHfGenerator(model_name="does-not-load")
    with pytest.raises(RuntimeError, match=r"\[bench\]"):
        gen.generate("Q", [_chunk()])


def test_local_hf_model_load_failure_does_not_become_mock(monkeypatch):
    def fake_pipeline(*_args, **_kwargs):
        raise OSError("model not found")

    monkeypatch.setattr(
        "rageval.pipeline.generator._import_transformers_pipeline",
        lambda: fake_pipeline,
    )
    gen = LocalHfGenerator(model_name="not-a-real-model")
    with pytest.raises(RuntimeError, match="does not fall back to the mock generator"):
        gen.generate("Q", [_chunk()])
    assert isinstance(gen, LocalHfGenerator)


def test_opt_in_yamls_load_without_secrets():
    openai = pipeline_config_from_yaml("configs/opt_in/openai_http.yaml")
    assert openai.opt_in is True
    assert openai.resource_note
    assert openai.generator.backend == "openai"
    assert openai.generator.api_key_env is None
    dumped = openai.model_dump_json()
    assert '"api_key"' not in dumped
    assert "sk-" not in dumped
    ollama = pipeline_config_from_yaml("configs/opt_in/ollama_http.yaml")
    assert ollama.generator.backend == "ollama"
    local = pipeline_config_from_yaml("configs/opt_in/local_hf.yaml")
    assert local.generator.backend == "local_hf"
