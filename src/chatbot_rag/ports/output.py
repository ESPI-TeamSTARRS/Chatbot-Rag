from abc import ABC, abstractmethod

from datetime import datetime

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


class RequestHistoryPort(ABC):
    """What the application needs to remember incoming requests and the documents they used."""

    @abstractmethod
    def record_request(self, received_at: datetime, content: str) -> int:
        """Store the request and return its id."""

    @abstractmethod
    def record_documents(self, request_id: int, paths: list[str]) -> None:
        """Register the documents (added to the known list if new) used to answer the request."""
