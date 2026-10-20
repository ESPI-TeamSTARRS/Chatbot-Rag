import pytest

from chatbot_rag.domain import HistoryError, IterationLimitError, LlmReply, LlmToolRequest, SearchHit
from chatbot_rag.usecases.diagnose import DiagnoseIncident
from fakes import FakeHistory


def diagnose_incident(trace, *, llm, search, writer, history=None, **options):
    return DiagnoseIncident(llm, search, writer, history or FakeHistory(), **options).execute(trace)


class ScriptedLlm:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def chat(self, messages, tools):
        self.calls += 1
        return self.replies.pop(0) if self.replies else self.replies_last

    replies_last = None


class LoopingLlm:
    def chat(self, messages, tools):
        return LlmReply(None, (LlmToolRequest("1", "search_docs", {"query": "x"}),))


class FakeSearch:
    def __init__(self, hits):
        self.hits, self.queries = hits, []

    def search(self, query, limit):
        self.queries.append(query)
        return self.hits


class FakeWriter:
    def __init__(self):
        self.reports = []

    def write(self, report):
        self.reports.append(report)
        return "actions-taken/x.md"


HIT = SearchHit("errors-cases/redis.md", "Restart sentinel.", 1.0)


def search_request(query="redis timeout"):
    return LlmReply(None, (LlmToolRequest("c1", "search_docs", {"query": query}),))


def test_final_answer_without_tools():
    result = diagnose_incident(
        "trace", llm=ScriptedLlm([LlmReply("No procedure found.")]), search=FakeSearch([]), writer=FakeWriter()
    )
    assert result.answer == "No procedure found."
    assert result.report_path is None


def test_search_then_answer():
    search = FakeSearch([HIT])
    llm = ScriptedLlm([search_request(), LlmReply("Restart sentinel.")])
    result = diagnose_incident("trace", llm=llm, search=search, writer=FakeWriter())
    assert search.queries == ["redis timeout"]
    assert result.answer == "Restart sentinel."


def test_report_assembled_from_code_owned_data():
    writer = FakeWriter()
    write = LlmReply(None, (LlmToolRequest("c2", "write_report", {"title": "Redis", "summary": "Restart it"}),))
    llm = ScriptedLlm([search_request(), write, LlmReply("Done.")])
    result = diagnose_incident("ERROR redis down", llm=llm, search=FakeSearch([HIT]), writer=writer)
    report = writer.reports[0]
    assert (report.title, report.summary, report.error_trace) == ("Redis", "Restart it", "ERROR redis down")
    assert [call.name for call in report.tool_calls] == ["search_docs"]
    assert "Restart sentinel." in report.tool_calls[0].result
    assert result.report_path == "actions-taken/x.md"


def test_iteration_cap():
    with pytest.raises(IterationLimitError):
        diagnose_incident("t", llm=LoopingLlm(), search=FakeSearch([]), writer=FakeWriter(), max_iterations=3)


def test_unknown_tool_is_reported_to_llm_not_crash():
    bad = LlmReply(None, (LlmToolRequest("c1", "rm_rf", {}),))
    llm = ScriptedLlm([bad, LlmReply("ok")])
    assert diagnose_incident("t", llm=llm, search=FakeSearch([]), writer=FakeWriter()).answer == "ok"


def test_request_and_documents_are_recorded():
    history = FakeHistory()
    llm = ScriptedLlm([search_request(), LlmReply("ok")])
    diagnose_incident("ERROR redis down", llm=llm, search=FakeSearch([HIT]), writer=FakeWriter(), history=history)
    assert [content for _, content in history.requests] == ["ERROR redis down"]
    assert history.requests[0][0].tzinfo is not None
    assert history.documents == [(1, ["errors-cases/redis.md"])]


class BrokenHistory:
    def record_request(self, received_at, content):
        raise HistoryError("db down")

    def record_documents(self, request_id, paths):
        raise HistoryError("db down")


def test_history_failure_does_not_break_the_diagnosis():
    llm = ScriptedLlm([search_request(), LlmReply("ok")])
    result = diagnose_incident("t", llm=llm, search=FakeSearch([HIT]), writer=FakeWriter(), history=BrokenHistory())
    assert result.answer == "ok"


def test_documents_failure_alone_does_not_break_the_diagnosis():
    class DocumentsDown(FakeHistory):
        def record_documents(self, request_id, paths):
            raise HistoryError("db down")

    llm = ScriptedLlm([search_request(), LlmReply("ok")])
    result = diagnose_incident("t", llm=llm, search=FakeSearch([HIT]), writer=FakeWriter(), history=DocumentsDown())
    assert result.answer == "ok"
