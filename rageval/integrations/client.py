"""HTTP client that captures returned answers and sources from sync/async agents."""
import functools
import inspect
import json
import time
from urllib.request import Request, urlopen


class RAGEvalClient:
    def __init__(self, url, public_token, admin_token, timeout=30):
        self.url, self.public_token, self.admin_token, self.timeout = url.rstrip('/'), public_token, admin_token, timeout

    def capture(self, row):
        request = Request(self.url + '/workspace/traces', data=json.dumps(row).encode(), headers={
            'Content-Type': 'application/json', 'X-RAGEVAL-API-TOKEN': self.public_token,
            'X-RAGEVAL-ADMIN-TOKEN': self.admin_token}, method='POST')
        with urlopen(request, timeout=self.timeout) as response:
            return json.load(response)

    def monitor(self, *, configuration, dataset_id, question_id):
        """Wrap an agent(question, ...) returning {answer, context_chunks, cost_usd?}.

        Evaluation failures propagate explicitly. Use question_id per benchmark item.
        Async calls send evaluation in a thread to avoid blocking the event loop.
        """
        def decorate(fn):
            def record(question, result, elapsed):
                self.capture(dict(question=question, answer=result['answer'], context_chunks=result['context_chunks'],
                    configuration=configuration, dataset_id=dataset_id, question_id=question_id,
                    latency_ms=elapsed, cost_usd=result.get('cost_usd')))
                return result
            if inspect.iscoroutinefunction(fn):
                @functools.wraps(fn)
                async def asynchronous(question, *args, **kwargs):
                    import asyncio
                    start = time.perf_counter()
                    result = await fn(question, *args, **kwargs)
                    return await asyncio.to_thread(record, question, result, (time.perf_counter()-start)*1000)
                return asynchronous
            @functools.wraps(fn)
            def synchronous(question, *args, **kwargs):
                start = time.perf_counter()
                result = fn(question, *args, **kwargs)
                return record(question, result, (time.perf_counter()-start)*1000)
            return synchronous
        return decorate
