import pytest

from chatbot_rag import main
from chatbot_rag.config import Setting
from chatbot_rag.domain import NotificationError
from chatbot_rag.logger import logger


@pytest.fixture(autouse=True)
def configured_environment(monkeypatch):
    logger.reset()
    monkeypatch.setitem(Setting.model_config, "env_file", None)
    monkeypatch.setenv("LLM_BASE_URL", "http://h/v1")
    monkeypatch.setenv("LLM_MODEL", "m")
    monkeypatch.setenv("N8N_WEBHOOK_URL", "http://n8n/webhook/x")
    monkeypatch.setattr(main.LokiRequestHistory, "check_available", lambda self: None)
    yield
    logger.reset()


def test_n8n_offline_aborts_startup_with_exit_code_4(monkeypatch, capsys):
    def down(self):
        raise NotificationError("n8n unavailable (ConnectError)")

    monkeypatch.setattr(main.N8nWebhookNotifier, "check_available", down)
    monkeypatch.setattr(main.uvicorn, "run", lambda *args, **kwargs: pytest.fail("must not serve"))
    assert main.main() == 4
    assert "n8n unavailable" in capsys.readouterr().err


def test_n8n_reachable_starts_the_server(monkeypatch):
    served = []
    monkeypatch.setattr(main.N8nWebhookNotifier, "check_available", lambda self: None)
    monkeypatch.setattr(main.uvicorn, "run", lambda app, **kwargs: served.append(app))
    assert main.main() == 0
    assert len(served) == 1
