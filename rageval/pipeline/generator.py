"""Generation layer supporting deterministic mock generators and optional HTTP LLMs."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from rageval.core.config import GeneratorConfig
from rageval.core.schemas import BenchmarkItem, RetrievedChunk


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
    """Generator for OpenAI / vLLM / Ollama compatible HTTP endpoints."""

    def __init__(self, api_key: str = "", base_url: str = "http://localhost:11434/v1", model: str = "llama3"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def generate(
        self,
        question: str,
        retrieved_chunks: List[RetrievedChunk],
        item: Optional[BenchmarkItem] = None,
    ) -> Tuple[str, int, int]:
        del item
        import httpx

        context_str = "\n\n".join([f"[{i+1}] {r.chunk.text}" for i, r in enumerate(retrieved_chunks)])
        prompt = (
            f"Context Information:\n{context_str}\n\n"
            f"Question: {question}\n\n"
            "Answer the question strictly based on the context above. Cite sources with bracketed numbers like [1]. "
            "If the context does not contain the answer, say 'I do not have sufficient information to answer.'"
        )

        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a factual RAG assistant. Never extrapolate beyond provided context."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
                data = res.json()
                answer = data["choices"][0]["message"]["content"]
                prompt_tokens = data.get("usage", {}).get("prompt_tokens", len(prompt.split()))
                comp_tokens = data.get("usage", {}).get("completion_tokens", len(answer.split()))
                return answer, prompt_tokens, comp_tokens
        except Exception as e:
            return f"Error contacting LLM endpoint: {e}", len(prompt.split()), 10


def get_generator(config: GeneratorConfig) -> BaseGenerator:
    if config.backend == "mock":
        return MockGenerator(mode=config.mock_mode, abstention_policy=config.abstention_policy)
    if config.backend in ("openai", "ollama"):
        return OpenAILikeGenerator(model=config.model_name)
    raise ValueError(
        f"Unknown generator backend {config.backend!r}. Supported backends: mock, openai, ollama. "
        "local_hf is not implemented; do not silently substitute another backend."
    )
