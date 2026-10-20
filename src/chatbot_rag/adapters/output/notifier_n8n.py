import httpx

from chatbot_rag.domain import NotificationError
from chatbot_rag.ports import ProcedureNotifierPort

TIMEOUT_SECONDS = 10


class N8nWebhookNotifier(ProcedureNotifierPort):
    """POSTs the error log and the procedure, as is, to an n8n webhook."""

    def __init__(self, url: str, client: httpx.Client | None = None):
        self._url = url
        self._client = client or httpx.Client(timeout=TIMEOUT_SECONDS)

    def notify(self, error_log: str, procedure: str) -> None:
        try:
            response = self._client.post(self._url, json={"error_log": error_log, "procedure": procedure})
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise NotificationError(f"n8n webhook unavailable ({error!r})") from error
