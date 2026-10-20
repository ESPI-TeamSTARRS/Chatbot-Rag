from dataclasses import dataclass


@dataclass(frozen=True)
class SearchHit:
    """A documentation file matching a search query."""

    path: str
    text: str
    score: float


@dataclass(frozen=True)
class LlmToolRequest:
    """A tool the LLM asks us to run."""

    id: str
    name: str
    arguments: dict


@dataclass(frozen=True)
class LlmReply:
    content: str | None
    tool_requests: tuple[LlmToolRequest, ...] = ()


@dataclass(frozen=True)
class DiagnosisResult:
    answer: str
