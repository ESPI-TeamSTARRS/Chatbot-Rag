import json
import uuid
from datetime import datetime, timezone

import httpx

from chatbot_rag.domain import HistoryError
from chatbot_rag.ports import RequestHistoryPort

PUSH_PATH = "/loki/api/v1/push"
TIMEOUT_SECONDS = 3
APP_LABEL = "chatbot-rag"


class LokiRequestHistory(RequestHistoryPort):
    """Sends each request (arrival time, content) and the documents it used to Loki as log lines.

    Streams: {app="chatbot-rag", event="request"} and {app="chatbot-rag", event="document_used"}.
    A line carries the request_id (generated here) so both events can be joined in LogQL.
    """

    def __init__(self, url: str, client: httpx.Client | None = None):
        self._push_url = url.rstrip("/") + PUSH_PATH
        self._client = client or httpx.Client(timeout=TIMEOUT_SECONDS)

    def record_request(self, received_at: datetime, content: str) -> str:
        request_id = str(uuid.uuid4())
        line = json.dumps({"request_id": request_id, "content": content}, ensure_ascii=False)
        self._push("request", [(received_at, line)])
        return request_id

    def record_documents(self, request_id: str, paths: list[str]) -> None:
        now = datetime.now(timezone.utc)
        lines = [
            (now, json.dumps({"request_id": request_id, "path": path}, ensure_ascii=False))
            for path in dict.fromkeys(paths)
        ]
        if lines:
            self._push("document_used", lines)

    def _push(self, event: str, entries: list[tuple[datetime, str]]) -> None:
        body = {
            "streams": [
                {
                    "stream": {"app": APP_LABEL, "event": event},
                    "values": [[str(int(at.timestamp() * 1_000_000_000)), line] for at, line in entries],
                }
            ]
        }
        try:
            self._client.post(self._push_url, json=body).raise_for_status()
        except httpx.HTTPError as error:
            raise HistoryError(f"Loki unavailable ({error!r})") from error
