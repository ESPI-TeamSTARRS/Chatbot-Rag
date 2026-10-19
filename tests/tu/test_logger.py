from datetime import datetime

import pytest

from chatbot_rag.domain import LlmReply
from chatbot_rag.logger import logger
from chatbot_rag.usecases.diagnose import DiagnoseIncident


@pytest.fixture(autouse=True)
def fresh_logger():
    logger.reset()
    yield
    logger.reset()


def test_enabled_logger_prints_timestamp_and_debug_message(capsys):
    logger.configure(enabled=True)
    logger.debug(message="hello")
    timestamp, message = capsys.readouterr().out.rstrip("\n").split(" [DEBUG]: ")
    datetime.fromisoformat(timestamp)
    assert message == "hello"


def test_disabled_or_unconfigured_logger_prints_nothing(capsys):
    logger.debug(message="before configure")
    logger.configure(enabled=False)
    logger.debug(message="hello")
    assert capsys.readouterr().out == ""


def test_logger_can_only_be_configured_once():
    logger.configure(enabled=True)
    with pytest.raises(RuntimeError):
        logger.configure(enabled=False)


def test_use_case_logs_its_steps(capsys):
    class Llm:
        def chat(self, messages, tools):
            return LlmReply("done")

    logger.configure(enabled=True)
    DiagnoseIncident(Llm(), None, None).execute("boom")
    out = capsys.readouterr().out
    assert "[DEBUG]: Diagnosis started" in out and "[DEBUG]: Final answer: 'done'" in out
