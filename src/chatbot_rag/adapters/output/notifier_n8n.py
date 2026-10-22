import httpx
from chatbot_rag.logger import logger
from chatbot_rag.config import load_setting
from chatbot_rag.domain import NotificationError
from chatbot_rag.ports import ProcedureNotifierPort

TIMEOUT_SECONDS = 10

config = load_setting()


def _format_email(error_log: str, procedure: str)->dict:
    return {
        "to": f"{config.RECIPIENT_EMAIL}",
        "subject": "[RAG] Erreurs détectées",
        "body": (
            "error_log: " +
            error_log +
            "\n\nprocedure: " +
            procedure +
            "\n\nCeci est un mail automatique, veuillez ne pas y répondre."
        )
    }


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
            email:dict = _format_email(error_log, procedure)
            logger.debug("Email envoyé à n8n : "+ str(email))
            response = self._client.post(
                self._url, json=email
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise NotificationError(f"n8n webhook unavailable ({error!r})") from error

