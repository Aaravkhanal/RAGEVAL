import asyncio
from rageval.integrations.client import RAGEvalClient


def test_sync_and_async_capture_preserve_result(monkeypatch):
    client = RAGEvalClient('https://example.com', 'public', 'admin')
    captured = []
    monkeypatch.setattr(client, 'capture', captured.append)
    result = {'answer':'answer','context_chunks':['source']}
    @client.monitor(configuration='a',dataset_id='d',question_id='q')
    def sync(question):
        return result
    @client.monitor(configuration='b',dataset_id='d',question_id='q')
    async def asynchronous(question):
        return result
    assert sync('question') is result
    assert asyncio.run(asynchronous('question')) is result
    assert [r['configuration'] for r in captured] == ['a','b']
    assert all(r['cost_usd'] is None and r['latency_ms'] >= 0 for r in captured)
