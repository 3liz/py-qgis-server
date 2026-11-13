""" Test streamed (chunked) responses through the zmq broker

    Regression test: when several requests were sent concurrently
    from the same client, multiple pollers were started on the client socket,
    messages could be processed out of order and chunks were silently
    lost (e.g. WFS GetFeature returning fewer features with a 200 status).

    Also check that data sent with the last chunk is not discarded.
"""
import asyncio
import shutil
import tempfile

from multiprocessing import Process

import pytest

from pyqgisserver.zeromq.broker import run_broker
from pyqgisserver.zeromq.client import AsyncClient
from pyqgisserver.zeromq.worker import RequestHandler, run_worker

NUM_CHUNKS = 200
NUM_WORKERS = 8
NUM_REQUESTS = 8


class StreamingHandler(RequestHandler):
    """ Mimic Qgis server streaming: one chunk per feature
    """
    # Data sent along with the end-of-stream message
    last_chunk = b""

    def handle_message(self):
        self.send(b"HEAD", True)
        for i in range(NUM_CHUNKS):
            self.send(b"%d" % i, True)
        self.send(self.last_chunk, False)


def _run_streaming_worker(address: str, last_chunk: bytes):
    StreamingHandler.last_chunk = last_chunk
    run_worker(address, StreamingHandler)


def _stop(p: Process):
    p.terminate()
    p.join(2)
    if p.is_alive():
        p.kill()
        p.join()


@pytest.fixture(params=[b"", b"LAST"], ids=["empty-last-chunk", "data-in-last-chunk"])
def broker_addresses(request: pytest.FixtureRequest):
    last_chunk = request.param
    # Keep path short: ipc endpoints are limited in length
    tmpdir = tempfile.mkdtemp(prefix="qgsrv")
    inaddr, outaddr = f"ipc://{tmpdir}/in", f"ipc://{tmpdir}/out"

    broker = Process(target=run_broker, args=(inaddr, outaddr), daemon=True)
    broker.start()
    workers = [
        Process(target=_run_streaming_worker, args=(outaddr, last_chunk), daemon=True)
        for _ in range(NUM_WORKERS)
    ]
    for w in workers:
        w.start()

    yield inaddr, last_chunk

    for p in (*workers, broker):
        _stop(p)
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_concurrent_streamed_responses(broker_addresses: tuple):
    """ Concurrent streamed responses must be complete and in order
    """
    address, last_chunk = broker_addresses

    async def run() -> list:
        client = AsyncClient(address)
        try:
            # Let workers connect
            await asyncio.sleep(1)

            async def fetch() -> tuple:
                response = await client.fetch(query="?test", timeout=10)
                chunks = [
                    chunk async for chunk in client.fetch_more(response, timeout=10)
                ]
                return response.data, chunks

            # Concurrent requests issued in the same event loop iteration
            return await asyncio.gather(*(fetch() for _ in range(NUM_REQUESTS)))
        finally:
            client.terminate()

    expected = [b"%d" % i for i in range(NUM_CHUNKS)]
    if last_chunk:
        expected.append(last_chunk)

    results = asyncio.run(run())
    assert len(results) == NUM_REQUESTS
    for head, chunks in results:
        assert head == b"HEAD"
        assert chunks == expected
