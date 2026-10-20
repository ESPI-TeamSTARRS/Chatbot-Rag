import socket
import subprocess
import sys
import time

import pytest

from chatbot_rag.adapters.output.search_mcp import McpDocSearch
from chatbot_rag.domain import SearchError

FAKE_SERVER = """
import sys
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fake-search", port=int(sys.argv[1]))
DOCS = [{"path": "redis.md", "text": "Restart the redis sentinel.", "score": 1.5}]


@mcp.tool()
def search_docs(query: str, limit: int = 5) -> list[dict]:
    return [doc for doc in DOCS if query in doc["text"].lower()][:limit]


mcp.run(transport="streamable-http")
"""


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def server_url():
    port = free_port()
    process = subprocess.Popen(
        [sys.executable, "-c", FAKE_SERVER, str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    deadline = time.time() + 30
    while time.time() < deadline:
        if process.poll() is not None:
            pytest.fail(f"fake MCP server exited: {process.stderr.read().decode()}")
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                break
        time.sleep(0.1)
    else:
        process.kill()
        pytest.fail("fake MCP server did not start")
    yield f"http://127.0.0.1:{port}/mcp"
    process.terminate()
    process.wait(timeout=10)


def test_search_goes_through_the_mcp_server(server_url):
    hits = McpDocSearch(server_url).search("redis", limit=3)
    assert [(hit.path, hit.text, hit.score) for hit in hits] == [
        ("redis.md", "Restart the redis sentinel.", 1.5)
    ]


def test_no_match_returns_empty(server_url):
    assert McpDocSearch(server_url).search("kubernetes", limit=3) == []


def test_unreachable_server_raises_search_error():
    with pytest.raises(SearchError):
        McpDocSearch(f"http://127.0.0.1:{free_port()}/mcp").search("redis", limit=3)
