import json

from openai import OpenAI, OpenAIError

from chatbot_rag.domain import LlmError, LlmReply, LlmToolRequest
from chatbot_rag.ports import LlmPort


class OpenAiCompatibleLlm(LlmPort):
    """LLM adapter for any server speaking the OpenAI chat-completions API (Ollama, vLLM...)."""

    def __init__(self, base_url: str, model: str, api_key: str = "not-needed"):
        self._client = OpenAI(base_url=base_url, api_key=api_key)
        self._model = model

    def chat(self, messages: list[dict], tools: list[dict]) -> LlmReply:
        try:
            response = self._client.chat.completions.create(
                model=self._model, messages=messages, tools=tools
            )
        except OpenAIError as error:
            raise LlmError(f"LLM request failed: {error}") from error
        message = response.choices[0].message
        tool_requests = tuple(self._to_tool_request(call) for call in message.tool_calls or ())
        return LlmReply(content=message.content, tool_requests=tool_requests)

    @classmethod
    def _to_tool_request(cls, call) -> LlmToolRequest:
        arguments = cls._parse_arguments(call.function.arguments)
        return LlmToolRequest(call.id, call.function.name, arguments)

    @staticmethod
    def _parse_arguments(raw: str | None) -> dict:
        try:
            parsed = json.loads(raw or "{}")
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
