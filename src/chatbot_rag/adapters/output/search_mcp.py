import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from chatbot_rag.domain import SearchError, SearchHit
from chatbot_rag.ports import DocSearchPort

SEARCH_TOOL = "search_docs"


class McpDocSearch(DocSearchPort):
    """Documentation search delegated to a remote MCP server (see ../mcp-server)."""

    def __init__(self, url: str):
        self._url = url

    def search(self, query: str, limit: int) -> list[SearchHit]:
        try:
            return asyncio.run(self._search(query, limit))
        except SearchError:
            raise
        except Exception as error:
            raise SearchError(f"Documentation search unavailable ({error!r})") from error

    async def _search(self, query: str, limit: int) -> list[SearchHit]:
        async with streamable_http_client(self._url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(SEARCH_TOOL, {"query": query, "limit": limit})
        if result.isError:
            raise SearchError(f"Search tool failed: {result.content}")
        return [
            SearchHit(item["path"], item["text"], float(item["score"]))
            for item in (result.structuredContent or {}).get("result", [])
        ]
