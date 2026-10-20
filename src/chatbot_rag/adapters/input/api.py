from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

from chatbot_rag.domain import IterationLimitError, LlmError, SearchError
from chatbot_rag.ports import DiagnoseIncidentPort


class InstructionRequest(BaseModel):
    instruction: str

    @field_validator("instruction")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("instruction must not be blank")
        return value


class InstructionResponse(BaseModel):
    answer: str
    report_path: str | None


class IncidentApi:
    """HTTP adapter: exposes the incident diagnosis use case through FastAPI."""

    def __init__(self, diagnose_incident: DiagnoseIncidentPort):
        self._diagnose_incident = diagnose_incident
        self.app = FastAPI(title="Chatbot RAG")
        self.app.post("/v1/traite-instruction-usager", response_model=InstructionResponse)(
            self._traite_instruction_usager
        )

    def _traite_instruction_usager(self, request: InstructionRequest) -> InstructionResponse:
        try:
            result = self._diagnose_incident.execute(request.instruction)
        except (IterationLimitError, LlmError, SearchError) as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
        return InstructionResponse(answer=result.answer, report_path=result.report_path)
