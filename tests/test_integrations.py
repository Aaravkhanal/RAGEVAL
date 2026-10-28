"""Unit tests for ecosystem adapters: decorator, LangChain callback, and LlamaIndex handler."""

import pytest
from rageval.integrations import monitor_rag, RAGEvalLangChainCallback, RAGEvalLlamaIndexHandler


def test_monitor_rag_decorator():
    @monitor_rag()
    def sample_rag_pipeline(query: str):
        context = ["ApexCloud achieved 78.2% gross margin in Q3 2024."]
        answer = "ApexCloud achieved 78.2% gross margin [1]."
        return {"answer": answer, "contexts": context}

    result = sample_rag_pipeline(query="What was the gross margin?")
    assert "rageval_evaluation" in result
    eval_res = result["rageval_evaluation"]
    assert eval_res.faithfulness_score == 1.0


def test_monitor_rag_fail_on_hallucination():
    @monitor_rag(fail_on_hallucination=True, hallucination_threshold=0.30)
    def hallucinatory_rag_pipeline(query: str):
        return {
            "answer": "ApexCloud relocated headquarters to an offshore volcanic island.",
            "contexts": ["ApexCloud reported regular quarterly financials in Delaware."],
        }

    with pytest.raises(ValueError, match="Generation failed hallucination check"):
        hallucinatory_rag_pipeline(query="Where is the company located?")


def test_langchain_callback():
    cb = RAGEvalLangChainCallback()
    cb.on_chain_start({}, {"query": "What is the margin?"})
    
    class MockDoc:
        page_content = "ApexCloud gross margin was 78.2%."

    cb.on_retriever_end([MockDoc()])
    cb.on_chain_end({"result": "The gross margin was 78.2% [1]."})

    assert cb.last_evaluation is not None
    assert cb.last_evaluation.faithfulness_score == 1.0


def test_llamaindex_handler():
    handler = RAGEvalLlamaIndexHandler()

    class MockNode:
        def get_content(self):
            return "HydraKV median read latency is 1.4 ms."

    class MockSourceNode:
        node = MockNode()

    class MockResponse:
        response = "HydraKV median latency is 1.4 ms [1]."
        source_nodes = [MockSourceNode()]

    res = handler.evaluate_response("What is HydraKV read latency?", MockResponse())
    assert res.faithfulness_score == 1.0
