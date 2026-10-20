import pytest

from chatbot_rag.domain import HistoryError, IterationLimitError, NotificationError, LlmReply, LlmToolRequest, SearchHit
from chatbot_rag.usecases.diagnose import DiagnoseIncident
from fakes import FakeHistory, FakeNotifier


def diagnose_incident(trace, *, llm, search, notifier=None, history=None, **options):
    return DiagnoseIncident(llm, search, notifier or FakeNotifier(), history or FakeHistory(), **options).execute(trace)


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


HIT = SearchHit("errors-cases/redis.md", "Restart sentinel.", 1.0)


def search_request(query="redis timeout"):
    return LlmReply(None, (LlmToolRequest("c1", "search_docs", {"query": query}),))


def test_final_answer_without_tools():
    result = diagnose_incident(
        "trace", llm=ScriptedLlm([LlmReply("No procedure found.")]), search=FakeSearch([])
    )
    assert result.answer == "No procedure found."


def test_search_then_answer():
    search = FakeSearch([HIT])
    llm = ScriptedLlm([search_request(), LlmReply("Restart sentinel.")])
    result = diagnose_incident("trace", llm=llm, search=search)
    assert search.queries == ["redis timeout"]
    assert result.answer == "Restart sentinel."


def test_error_log_and_procedure_are_sent_as_is_to_the_notifier():
    notifier = FakeNotifier()
    llm = ScriptedLlm([search_request(), LlmReply("Restart sentinel.")])
    diagnose_incident("ERROR redis down", llm=llm, search=FakeSearch([HIT]), notifier=notifier)
    assert notifier.sent == [("ERROR redis down", "Restart sentinel.")]


def test_notifier_failure_does_not_break_the_diagnosis():
    class Down:
        def notify(self, error_log, procedure):
            raise NotificationError("n8n down")

    result = diagnose_incident("t", llm=ScriptedLlm([LlmReply("ok")]), search=FakeSearch([]), notifier=Down())
    assert result.answer == "ok"


def test_iteration_cap():
    with pytest.raises(IterationLimitError):
        diagnose_incident("t", llm=LoopingLlm(), search=FakeSearch([]), max_iterations=3)


def test_unknown_tool_is_reported_to_llm_not_crash():
    bad = LlmReply(None, (LlmToolRequest("c1", "rm_rf", {}),))
    llm = ScriptedLlm([bad, LlmReply("ok")])
    assert diagnose_incident("t", llm=llm, search=FakeSearch([])).answer == "ok"


def test_request_and_documents_are_recorded():
    history = FakeHistory()
    llm = ScriptedLlm([search_request(), LlmReply("ok")])
    diagnose_incident("ERROR redis down", llm=llm, search=FakeSearch([HIT]), history=history)
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
    result = diagnose_incident("t", llm=llm, search=FakeSearch([HIT]), history=BrokenHistory())
    assert result.answer == "ok"


def test_documents_failure_alone_does_not_break_the_diagnosis():
    class DocumentsDown(FakeHistory):
        def record_documents(self, request_id, paths):
            raise HistoryError("db down")

    llm = ScriptedLlm([search_request(), LlmReply("ok")])
    result = diagnose_incident("t", llm=llm, search=FakeSearch([HIT]), history=DocumentsDown())
    assert result.answer == "ok"
