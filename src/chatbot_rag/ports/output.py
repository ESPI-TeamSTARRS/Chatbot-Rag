from abc import ABC, abstractmethod

from chatbot_rag.domain import LlmReply, Report, SearchHit


class LlmPort(ABC):
    """What the application needs from a language model."""

    @abstractmethod
    def chat(self, messages: list[dict], tools: list[dict]) -> LlmReply: ...


class DocSearchPort(ABC):
    """What the application needs from a documentation search engine."""

    @abstractmethod
    def search(self, query: str, limit: int) -> list[SearchHit]: ...


class ReportWriterPort(ABC):
    """What the application needs to persist an incident report."""

    @abstractmethod
    def write(self, report: Report) -> str:
        """Persist the report and return its location."""
