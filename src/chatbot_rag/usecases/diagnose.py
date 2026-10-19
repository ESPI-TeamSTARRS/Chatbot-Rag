import json

from chatbot_rag.domain import (
    DiagnosisResult,
    IterationLimitError,
    LlmReply,
    LlmToolRequest,
    Report,
    SearchHit,
    ToolCall,
)
from chatbot_rag.ports import (
    DiagnoseIncidentPort,
    DocSearchPort,
    LlmPort,
    ReportWriterPort,
)
from chatbot_rag.logger import logger
from chatbot_rag.usecases.tools import SEARCH_DOCS, TOOL_SCHEMAS, WRITE_REPORT

SYSTEM_PROMPT = (
    "You are an incident-response assistant. You receive an error trace. Call the search_docs tool "
    "once: it returns the full content of the 5 most relevant documents. Read them to find the "
    "documented procedure for this case, answer with the procedure to follow, and "
    "call write_report once with a title and a summary. If the documentation has a 'Report' "
    "section that specifies the report name, use exactly that name as the title; otherwise choose "
    "a short, descriptive title yourself. If no documented procedure exists, say so. "
    "Never claim that a remediation was executed."
)
SEARCH_LIMIT = 5
DEFAULT_MAX_ITERATIONS = 8


class IncidentSession:
    """State of one diagnosis: the LLM conversation, the tool journal and the report location."""

    def __init__(self, trace: str):
        self.trace = trace
        self.messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": trace},
        ]
        self.journal: list[ToolCall] = []
        self.report_path: str | None = None

    def add_assistant_reply(self, reply: LlmReply) -> None:
        self.messages.append(
            {
                "role": "assistant",
                "content": reply.content,
                "tool_calls": [self._tool_call_message(request) for request in reply.tool_requests],
            }
        )

    def add_tool_result(self, request: LlmToolRequest, result: str) -> None:
        self.messages.append({"role": "tool", "tool_call_id": request.id, "content": result})

    def record_tool_call(self, request: LlmToolRequest, result: str) -> None:
        self.journal.append(ToolCall(request.name, request.arguments, result))

    def build_report(self, title: str, summary: str) -> Report:
        return Report(title, summary, self.trace, tuple(self.journal))

    @staticmethod
    def _tool_call_message(request: LlmToolRequest) -> dict:
        return {
            "id": request.id,
            "type": "function",
            "function": {"name": request.name, "arguments": json.dumps(request.arguments)},
        }


class DiagnoseIncident(DiagnoseIncidentPort):
    """Asks the LLM to diagnose an error trace, letting it search the docs and write a report."""

    def __init__(
        self,
        llm: LlmPort,
        search: DocSearchPort,
        writer: ReportWriterPort,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ):
        self._llm = llm
        self._search = search
        self._writer = writer
        self._max_iterations = max_iterations

    def execute(self, trace: str) -> DiagnosisResult:
        logger.debug(
            message=f"Diagnosis started, trace: {trace!r}"
        )
        session = IncidentSession(trace)
        for iteration in range(1, self._max_iterations + 1):
            logger.debug(
                message=f"LLM call {iteration}/{self._max_iterations}"
            )
            reply = self._llm.chat(session.messages, TOOL_SCHEMAS)
            if not reply.tool_requests:
                logger.debug(
                    message=f"Final answer: {reply.content!r}"
                )
                return DiagnosisResult(reply.content or "", session.report_path)
            session.add_assistant_reply(reply)
            for request in reply.tool_requests:
                session.add_tool_result(request, self._run_tool(request, session))
        logger.debug(
            message="Iteration limit reached"
        )
        raise IterationLimitError(
            f"Iteration limit of {self._max_iterations} reached without a final answer"
        )

    def _run_tool(self, request: LlmToolRequest, session: IncidentSession) -> str:
        logger.debug(
            message=f"Tool requested: {request.name} {request.arguments}"
        )
        if request.name == WRITE_REPORT:
            result = self._write_report(request.arguments, session)
        else:
            result = self._run_journaled_tool(request, session)
        logger.debug(
            message=f"Tool result ({request.name}): {result!r}"
        )
        return result

    def _run_journaled_tool(self, request: LlmToolRequest, session: IncidentSession) -> str:
        if request.name == SEARCH_DOCS:
            result = self._search_docs(request.arguments)
        else:
            result = f"Error: unknown tool '{request.name}'"
        session.record_tool_call(request, result)
        return result

    def _search_docs(self, arguments: dict) -> str:
        query = arguments.get("query")
        logger.debug(
            message=f"Tool requested: {SEARCH_DOCS} {query}"
        )
        if not isinstance(query, str) or not query.strip():
            raise Exception("Error: 'query' must be a non-empty string")
        return self._format_hits(self._search.search(query, SEARCH_LIMIT))

    def _write_report(self, arguments: dict, session: IncidentSession) -> str:
        try:
            report = session.build_report(arguments["title"], arguments["summary"])
            session.report_path = self._writer.write(report)
        except Exception as error:  # reported back to the LLM, which may retry
            raise Exception( f"Error: could not write report ({error!r})")
        return f"Report written to {session.report_path}"

    @staticmethod
    def _format_hits(hits: list[SearchHit]) -> str:
        if not hits:
            return "No matching documents."
        return "\n\n".join(DiagnoseIncident._format_hit(hit) for hit in hits)

    @staticmethod
    def _format_hit(hit: SearchHit) -> str:
        return f"[{hit.path}]\n{hit.text}"
