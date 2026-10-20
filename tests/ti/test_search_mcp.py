import os
import socket
import subprocess
import time
from pathlib import Path

import pytest

from chatbot_rag.adapters.output.search_mcp import McpDocSearch
from chatbot_rag.domain import SearchError

SERVER_DIR = Path(__file__).parents[2] / "mcp-bm25"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def server_url(tmp_path):
    (tmp_path / "redis.md").write_text("# Redis timeout\n\nRestart the redis sentinel.\n")
    port = free_port()
    env = {**os.environ, "DOCS_PATH": str(tmp_path), "PORT": str(port)}
    process = subprocess.Popen(
        ["uv", "run", "--project", str(SERVER_DIR), "bm25-mcp"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.time() + 30
    while time.time() < deadline:
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                break
        time.sleep(0.2)
    yield f"http://127.0.0.1:{port}/mcp"
    process.terminate()
    process.wait(timeout=10)


def test_search_goes_through_the_mcp_server(server_url):
    hits = McpDocSearch(server_url).search("redis sentinel", limit=3)
    assert [hit.path for hit in hits] == ["redis.md"]
    assert "Restart the redis sentinel." in hits[0].text


def test_no_match_returns_empty(server_url):
    assert McpDocSearch(server_url).search("kubernetes", limit=3) == []


def test_unreachable_server_raises_search_error():
    with pytest.raises(SearchError):
        McpDocSearch(f"http://127.0.0.1:{free_port()}/mcp").search("redis", limit=3)
