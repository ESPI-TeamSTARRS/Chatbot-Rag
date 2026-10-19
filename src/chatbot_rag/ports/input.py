from abc import ABC, abstractmethod

from chatbot_rag.domain import DiagnosisResult


class DiagnoseIncidentPort(ABC):
    """What the outside world (API, CLI...) can ask of the application."""

    @abstractmethod
    def execute(self, trace: str) -> DiagnosisResult: ...
