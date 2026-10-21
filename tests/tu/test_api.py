from fastapi.testclient import TestClient

from chatbot_rag.adapters.input.api import IncidentApi
from chatbot_rag.domain import DiagnosisResult, IterationLimitError, LlmError, NotificationError

URL = "/v1/traite-instruction-usager"


class FakeUseCase:
    def __init__(self, handle):
        self._handle = handle

    def execute(self, trace):
        return self._handle(trace)


def client(handle):
    return TestClient(IncidentApi(FakeUseCase(handle)).app)


def test_health_returns_ok_without_calling_use_case():
    calls = []
    response = client(lambda t: calls.append(t)).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert calls == []


def test_returns_answer():
    calls = []

    def handle(trace):
        calls.append(trace)
        return DiagnosisResult("Restart it.")

    response = client(handle).post(URL, json={"instruction": "ERROR boom"})
    assert response.status_code == 200
    assert response.json() == {"answer": "Restart it."}
    assert calls == ["ERROR boom"]


def test_missing_or_blank_instruction_is_422_and_handler_not_called():
    calls = []
    test_client = client(lambda t: calls.append(t))
    assert test_client.post(URL, json={}).status_code == 422
    assert test_client.post(URL, json={"instruction": "   "}).status_code == 422
    assert calls == []


def test_iteration_limit_and_llm_errors_are_502():
    def limit(trace):
        raise IterationLimitError("Iteration limit of 8 reached")

    def down(trace):
        raise LlmError("LLM request failed")

    response = client(limit).post(URL, json={"instruction": "x"})
    assert response.status_code == 502 and "Iteration limit" in response.json()["detail"]
    assert client(down).post(URL, json={"instruction": "x"}).status_code == 502


def test_n8n_failure_is_500_without_stacktrace():
    def down(trace):
        raise NotificationError("n8n webhook unavailable")

    response = client(down).post(URL, json={"instruction": "x"})
    assert response.status_code == 500
    assert response.json()["detail"] == "n8n webhook unavailable"
