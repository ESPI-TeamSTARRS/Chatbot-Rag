import httpx

from chatbot_rag.domain import NotificationError
from chatbot_rag.ports import ProcedureNotifierPort

TIMEOUT_SECONDS = 10


class N8nWebhookNotifier(ProcedureNotifierPort):
    """POSTs the error log and the procedure, as is, to an n8n webhook."""

    def __init__(self, url: str, client: httpx.Client | None = None):
        self._url = url
        self._client = client or httpx.Client(timeout=TIMEOUT_SECONDS)

    def check_available(self) -> None:
        """Only the host must answer: a POST-only webhook answers 404/405 to a GET, which is fine."""
        try:
            self._client.get(self._url)
        except httpx.HTTPError as error:
            raise NotificationError(f"n8n unavailable ({error!r})") from error

    def notify(self, error_log: str, procedure: str) -> None:
        try:
            response = self._client.post(
                self._url, json={"error_log": error_log, "procedure": procedure}
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise NotificationError(f"n8n webhook unavailable ({error!r})") from error
