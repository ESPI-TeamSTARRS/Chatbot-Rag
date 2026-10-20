import json
from datetime import datetime, timezone

import httpx
import pytest

from chatbot_rag.adapters.output.history_loki import LokiRequestHistory
from chatbot_rag.domain import HistoryError


def history(handler):
    return LokiRequestHistory("http://loki:3100/", httpx.Client(transport=httpx.MockTransport(handler)))


def test_request_is_pushed_with_arrival_timestamp_and_content():
    pushed = []

    def handler(request):
        pushed.append(request)
        return httpx.Response(204)

    received_at = datetime(2026, 10, 20, 8, 0, 0, tzinfo=timezone.utc)
    request_id = history(handler).record_request(received_at, "ERROR boom")
    assert str(pushed[0].url) == "http://loki:3100/loki/api/v1/push"
    stream = json.loads(pushed[0].content)["streams"][0]
    assert stream["stream"] == {"app": "chatbot-rag", "event": "request"}
    timestamp, line = stream["values"][0]
    assert timestamp == str(int(received_at.timestamp() * 1_000_000_000))
    assert json.loads(line) == {"request_id": request_id, "content": "ERROR boom"}


def test_each_distinct_document_is_pushed_once():
    pushed = []

    def handler(request):
        pushed.append(json.loads(request.content))
        return httpx.Response(204)

    history(handler).record_documents("r1", ["a.md", "a.md", "b.md"])
    stream = pushed[0]["streams"][0]
    assert stream["stream"]["event"] == "document_used"
    assert [json.loads(line)["path"] for _, line in stream["values"]] == ["a.md", "b.md"]


def test_no_documents_pushes_nothing():
    history(lambda request: pytest.fail("no push expected")).record_documents("r1", [])


def test_loki_down_or_rejecting_raises_history_error():
    with pytest.raises(HistoryError):
        history(lambda request: httpx.Response(500)).record_request(datetime.now(timezone.utc), "x")

    def refused(request):
        raise httpx.ConnectError("refused")

    with pytest.raises(HistoryError):
        history(refused).record_documents("r1", ["a.md"])


def test_response_status_code_is_pushed_and_logged(capsys):
    pushed = []

    def handler(request):
        pushed.append(json.loads(request.content))
        return httpx.Response(204)

    history(handler).record_response("r1", 502)
    stream = pushed[0]["streams"][0]
    assert stream["stream"]["event"] == "response"
    assert json.loads(stream["values"][0][1]) == {"request_id": "r1", "status_code": 502}
    assert "enregistrement dans loki ..." in capsys.readouterr().out


def test_check_available_calls_ready_and_raises_when_loki_is_down():
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(200, text="ready")

    history(handler).check_available()
    assert calls == ["http://loki:3100/ready"]

    with pytest.raises(HistoryError):
        history(lambda request: httpx.Response(503)).check_available()

    def refused(request):
        raise httpx.ConnectError("refused")

    with pytest.raises(HistoryError):
        history(refused).check_available()
