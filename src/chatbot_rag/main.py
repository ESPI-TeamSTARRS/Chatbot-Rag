import sys

import uvicorn
from fastapi import FastAPI

from chatbot_rag.adapters.input.api import IncidentApi
from chatbot_rag.adapters.output.llm_openai import OpenAiCompatibleLlm
from chatbot_rag.adapters.output.report_markdown import MarkdownReportWriter
from chatbot_rag.adapters.output.search_mcp import McpDocSearch
from chatbot_rag.config import ConfigError, load_setting
from chatbot_rag.logger import logger
from chatbot_rag.usecases.diagnose import DiagnoseIncident


def build_app() -> FastAPI:
    """Composition root: the only place where adapters are wired to the use case."""
    config = load_setting()
    logger.configure(enabled=config.DEBUG)
    use_case = DiagnoseIncident(
        llm=OpenAiCompatibleLlm(config.LLM_BASE_URL, config.LLM_MODEL),
        search=McpDocSearch(config.SEARCH_MCP_URL),
        writer=MarkdownReportWriter(config.DOCS_PATH / "actions-taken"),
    )
    return IncidentApi(use_case).app


def main() -> int:
    try:
        app = build_app()
    except ConfigError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 2
    uvicorn.run(app, host="0.0.0.0", port=8000)
    return 0


if __name__ == "__main__":
    sys.exit(main())
