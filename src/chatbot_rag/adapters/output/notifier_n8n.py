import html

import httpx
from markdown_it import MarkdownIt

from chatbot_rag.config import load_setting
from chatbot_rag.domain import NotificationError
from chatbot_rag.logger import logger
from chatbot_rag.ports import ProcedureNotifierPort

TIMEOUT_SECONDS = 10

config = load_setting()

# html disabled: the procedure comes from an LLM reading untrusted docs, raw HTML must stay escaped.
_markdown = MarkdownIt("commonmark", {"html": False})


def _format_email(error_log: str, procedure: str)->dict:
    return {
        "to": f"{config.RECIPIENT_EMAIL}",
        "subject": "[RAG] Erreurs détectées",
        "body": (
            "<h1>Une erreur a été détectée par le Machine Learning</h1>"
            f"<pre>{html.escape(error_log)}</pre>"
            "<h1>La procédure à suivre</h1>"
            f"{_markdown.render(procedure)}"
            "<p>Ceci est un mail automatique, veuillez ne pas y répondre.</p>"
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
                self._url, json=email, headers={"X-Mail-Secret": config.N8N_TOKEN}
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise NotificationError(f"n8n webhook unavailable ({error!r})") from error

