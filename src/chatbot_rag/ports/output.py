from abc import ABC, abstractmethod

from datetime import datetime

from chatbot_rag.domain import LlmReply, SearchHit


class LlmPort(ABC):
    """What the application needs from a language model."""

    @abstractmethod
    def chat(self, messages: list[dict], tools: list[dict]) -> LlmReply: ...


class DocSearchPort(ABC):
    """What the application needs from a documentation search engine."""

    @abstractmethod
    def search(self, query: str, limit: int) -> list[SearchHit]: ...


class ProcedureNotifierPort(ABC):
    """What the application needs to hand the procedure to follow over to the outside world."""

    @abstractmethod
    def notify(self, error_log: str, procedure: str) -> None:
        """Send the error log received and the procedure to follow, both as is."""


class RequestHistoryPort(ABC):
    """What the application needs to remember incoming requests and the documents they used."""

    @abstractmethod
    def record_request(self, received_at: datetime, content: str) -> str:
        """Store the request and return its id."""

    @abstractmethod
    def record_documents(self, request_id: str, paths: list[str]) -> None:
        """Record the documents used to answer the request."""
