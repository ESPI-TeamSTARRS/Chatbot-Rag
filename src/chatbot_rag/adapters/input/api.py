import traceback

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from chatbot_rag.adapters.input.dto import ContexteIncidentDTO
from chatbot_rag.domain import (
    IterationLimitError,
    LlmError,
    NotificationError,
    SearchError,
)
from chatbot_rag.logger import logger
from chatbot_rag.ports import DiagnoseIncidentPort


class InstructionResponse(BaseModel):
    answer: str


class IncidentApi:
    """HTTP adapter: exposes the incident diagnosis use case through FastAPI."""

    def __init__(self, diagnose_incident: DiagnoseIncidentPort):
        self._diagnose_incident = diagnose_incident
        self.app = FastAPI(title="Chatbot RAG")
        self.app.post("/v1/handles-a-detected-error", response_model=InstructionResponse)(
            self._handles_a_detected_error
        )
        self.app.get("/health")(self._health)

    def _health(self) -> dict[str, str]:
        return {"status": "ok"}

    def _handles_a_detected_error(self, request: ContexteIncidentDTO) -> InstructionResponse:
        try:
            result = self._diagnose_incident.execute(request.to_trace())
        except (IterationLimitError, LlmError, SearchError) as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
        except NotificationError as error:
            stacktrace = traceback.format_exc()
            logger.warning(message=f"n8n unreachable:\n{stacktrace}")
            raise HTTPException(status_code=500, detail=str(error)) from error
        return InstructionResponse(answer=result.answer)
