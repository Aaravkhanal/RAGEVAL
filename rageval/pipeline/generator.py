"""Generation layer: blinded mock, OpenAI-like HTTP, and optional local Hugging Face."""

from __future__ import annotations

import os
import time
import re
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple

from rageval.core.config import GeneratorConfig
from rageval.core.schemas import BenchmarkItem, RetrievedChunk

OPENAI_DEFAULT_BASE_URL = "https://api.openai.com/v1"
OLLAMA_DEFAULT_BASE_URL = "http://127.0.0.1:11434/v1"
SUPPORTED_BACKENDS = ("mock", "openai", "ollama", "local_hf")


class BaseGenerator(ABC):
    @abstractmethod
    def generate(
        self,
        question: str,
        retrieved_chunks: List[RetrievedChunk],
        item: Optional[BenchmarkItem] = None,
    ) -> Tuple[str, int, int]:
        """Returns (generated_answer, prompt_tokens, completion_tokens).

        Implementations must not read gold labels, test_type, or expected_abstention
        from `item`. `item` is accepted only for API compatibility.
        """


def build_rag_prompt(question: str, retrieved_chunks: List[RetrievedChunk]) -> str:
    """Prompt from question + retrieved text only. Never include gold item fields."""
    if retrieved_chunks:
        context_str = "\n\n".join(
            f"[{i + 1}] {row.chunk.text}" for i, row in enumerate(retrieved_chunks)
        )
    else:
        context_str = "(no retrieved context)"
    return (
        f"Context Information:\n{context_str}\n\n"
        f"Question: {question}\n\n"
        "Answer the question strictly based on the context above. Cite sources with "
        "bracketed numbers like [1]. If the context does not contain the answer, say "
        "'I do not have sufficient information to answer.'"
    )


def default_base_url(backend: str) -> str:
    if backend == "openai":
        return OPENAI_DEFAULT_BASE_URL
    return OLLAMA_DEFAULT_BASE_URL


def resolve_api_key(backend: str, api_key_env: Optional[str] = None) -> str:
    """Read a key from the environment. Never from YAML."""
    names: List[str] = []
    if api_key_env:
        names.append(api_key_env)
    if backend == "openai":
        names.extend(["OPENAI_API_KEY", "NVIDIA_API_KEY", "RAGEVAL_API_KEY"])
    seen = set()
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        value = os.environ.get(name)
        if value:
            return value
    if backend == "openai":
        raise RuntimeError(
            "openai backend requires NVIDIA_API_KEY, OPENAI_API_KEY, or RAGEVAL_API_KEY "
            "in the environment (or a gitignored .env). Do not put API keys in YAML or git."
        )
    return ""


def _httpx_client(timeout: float):
    try:
        import httpx
    except ImportError as exc:
        raise RuntimeError(
            'openai/ollama backends require httpx. Install with pip install -e ".[api]"'
        ) from exc
    return httpx.Client(timeout=timeout)


def _import_transformers_pipeline():
    try:
        from transformers import pipeline
    except ImportError as exc:
        raise RuntimeError(
            'local_hf requires torch and transformers. Install with pip install -e ".[bench]"'
        ) from exc
    return pipeline


class MockGenerator(BaseGenerator):
    """Deterministic generator for tests. Blind to gold benchmark fields."""

    def __init__(self, mode: str = "faithful", abstention_policy: str = "empty_context"):
        self.mode = mode
        self.abstention_policy = abstention_policy

    def generate(
        self,
        question: str,
        retrieved_chunks: List[RetrievedChunk],
        item: Optional[BenchmarkItem] = None,
    ) -> Tuple[str, int, int]:
        del item  # gold labels are intentionally unused

        if self.abstention_policy == "empty_context" and not retrieved_chunks:
            answer = "I do not have sufficient information in the provided context to answer this question."
            return answer, 50, len(answer.split())

        if not retrieved_chunks:
            answer = "No retrieved context was available."
            return answer, 20, len(answer.split())

        top_chunk = retrieved_chunks[0].chunk
        chunk_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", top_chunk.text) if s.strip()]

        if self.mode == "faithful":
            chosen_facts = chunk_sentences[:2]
            cited_statements = []
            for i, stmt in enumerate(chosen_facts, start=1):
                citation_idx = min(i, len(retrieved_chunks))
                cited_statements.append(f"{stmt} [{citation_idx}]")
            answer = " ".join(cited_statements)

        elif self.mode == "hallucinatory":
            fact = chunk_sentences[0] if chunk_sentences else "The system operates as documented."
            answer = (
                f"{fact} [1] "
                f"Additionally, the platform processed 10 billion external transactions in 2025 [1]. "
                f"Moreover, the system automatically won the International Turing Excellence Prize in 2024."
            )

        elif self.mode == "contradictory":
            fact = chunk_sentences[0] if chunk_sentences else "The service operates continuously."
            contradiction = fact.replace("increased", "declined").replace("78.2%", "12.4%").replace("14.8", "2.1")
            if contradiction == fact:
                contradiction = f"Contrary to initial reports, {fact.lower()} was completely discontinued."
            answer = f"{contradiction} [1]"

        else:
            fact1 = chunk_sentences[0] if chunk_sentences else "The system operates as designed."
            answer = f"{fact1} [1] In contrast, undisclosed secondary benchmarks revealed zero reliability under load."

        prompt_tokens = sum(len(c.chunk.text.split()) for c in retrieved_chunks) + len(question.split()) + 30
        completion_tokens = len(answer.split())
        return answer, prompt_tokens, completion_tokens


class OpenAILikeGenerator(BaseGenerator):
    """OpenAI / vLLM / Ollama compatible HTTP. Keys come from the environment."""

    def __init__(
        self,
        *,
        api_key: str = "",
        base_url: str = OPENAI_DEFAULT_BASE_URL,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        max_tokens: int = 512,
        timeout: float = 60.0,
        max_retries: int = 2,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max(0, int(max_retries))

    def generate(
        self,
        question: str,
        retrieved_chunks: List[RetrievedChunk],
        item: Optional[BenchmarkItem] = None,
    ) -> Tuple[str, int, int]:
        del item
        prompt = build_rag_prompt(question, retrieved_chunks)
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a factual RAG assistant. Never extrapolate beyond provided context.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        url = f"{self.base_url}/chat/completions"
        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError(
                'openai/ollama backends require httpx. Install with pip install -e ".[api]"'
            ) from exc
        retryable = {429, 502, 503, 504}
        response = None
        last_error: Optional[BaseException] = None
        attempts = 1 + self.max_retries
        for attempt in range(1, attempts + 1):
            try:
                with _httpx_client(self.timeout) as client:
                    response = client.post(url, json=payload, headers=headers)
            except httpx.RequestError as exc:
                last_error = exc
                if attempt < attempts:
                    time.sleep(min(8.0, 0.25 * (2 ** attempt)))
                    continue
                raise RuntimeError(f"LLM HTTP request failed for {url}: {exc}") from exc
            if response.status_code in retryable and attempt < attempts:
                time.sleep(min(8.0, 0.25 * (2 ** attempt)))
                continue
            break
        if response is None:
            raise RuntimeError(f"LLM HTTP request failed for {url}: {last_error}")
        if response.status_code >= 400:
            snippet = (response.text or "")[:200]
            raise RuntimeError(f"LLM HTTP {response.status_code} from {url}: {snippet}")
        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(f"LLM HTTP response from {url} was not JSON") from exc
        try:
            message = data["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"LLM HTTP response from {url} missing choices[0].message") from exc
        answer = _message_text(message)
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError(
                f"LLM HTTP response from {url} had empty content "
                "(and no reasoning_content)"
            )
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        prompt_tokens = int(usage.get("prompt_tokens") or len(prompt.split()))
        completion_tokens = int(usage.get("completion_tokens") or len(answer.split()))
        return answer, prompt_tokens, completion_tokens


class LocalHfGenerator(BaseGenerator):
    """Lazy transformers text-generation. Missing torch/model is a hard failure."""

    def __init__(
        self,
        *,
        model_name: str,
        temperature: float = 0.0,
        max_tokens: int = 512,
        device: str = "cpu",
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.device = device
        self._pipeline: Any = None

    def _build_pipeline(self):
        try:
            pipeline = _import_transformers_pipeline()
            return pipeline(
                "text-generation",
                model=self.model_name,
                device=self.device,
            )
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load local_hf model {self.model_name!r}. "
                'Install with pip install -e ".[bench]" and check the model id. '
                "local_hf does not fall back to the mock generator."
            ) from exc

    def generate(
        self,
        question: str,
        retrieved_chunks: List[RetrievedChunk],
        item: Optional[BenchmarkItem] = None,
    ) -> Tuple[str, int, int]:
        del item
        prompt = build_rag_prompt(question, retrieved_chunks)
        if self._pipeline is None:
            self._pipeline = self._build_pipeline()
        kwargs: dict = {
            "max_new_tokens": self.max_tokens,
            "return_full_text": False,
        }
        if self.temperature and self.temperature > 0:
            kwargs["do_sample"] = True
            kwargs["temperature"] = self.temperature
        else:
            kwargs["do_sample"] = False
        try:
            outputs = self._pipeline(prompt, **kwargs)
        except Exception as exc:
            raise RuntimeError(f"local_hf generation failed for {self.model_name!r}: {exc}") from exc
        answer = _text_from_pipeline_output(outputs)
        prompt_tokens = len(prompt.split())
        completion_tokens = len(answer.split())
        tokenizer = getattr(self._pipeline, "tokenizer", None)
        if tokenizer is not None:
            try:
                prompt_tokens = len(tokenizer.encode(prompt))
                completion_tokens = len(tokenizer.encode(answer))
            except Exception:
                pass
        return answer, prompt_tokens, completion_tokens


def _message_text(message: Any) -> str:
    """OpenAI content, or NVIDIA reasoning_content when content is empty."""
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content
    reasoning = message.get("reasoning_content")
    if isinstance(reasoning, str) and reasoning.strip():
        return reasoning.strip()
    if isinstance(content, str):
        return content
    return ""


def _text_from_pipeline_output(outputs: Any) -> str:
    if isinstance(outputs, list) and outputs:
        first = outputs[0]
        if isinstance(first, dict):
            text = first.get("generated_text") or first.get("summary_text")
            if isinstance(text, str) and text.strip():
                return text.strip()
        elif isinstance(first, str) and first.strip():
            return first.strip()
    raise RuntimeError("local_hf pipeline returned no generated text")


def get_generator(config: GeneratorConfig) -> BaseGenerator:
    backend = (config.backend or "mock").strip()
    if backend == "mock":
        return MockGenerator(mode=config.mock_mode, abstention_policy=config.abstention_policy)
    if backend in {"openai", "ollama"}:
        return OpenAILikeGenerator(
            api_key=resolve_api_key(backend, config.api_key_env),
            base_url=config.base_url or default_base_url(backend),
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=float(config.timeout_s or 60.0),
            max_retries=int(config.max_retries if config.max_retries is not None else 2),
        )
    if backend == "local_hf":
        return LocalHfGenerator(
            model_name=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            device=config.device,
        )
    raise ValueError(
        f"Unknown generator backend {backend!r}. Supported backends: {', '.join(SUPPORTED_BACKENDS)}."
    )
