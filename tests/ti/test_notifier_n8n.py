import json

import httpx
import pytest

from chatbot_rag.adapters.output.notifier_n8n import N8nWebhookNotifier
from chatbot_rag.domain import NotificationError

URL = "http://n8n/webhook/incident"


def notifier(handler):
    return N8nWebhookNotifier(URL, httpx.Client(transport=httpx.MockTransport(handler)))


def test_posts_error_log_and_procedure_as_is():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200)

    notifier(handler).notify("ERROR boom\n  at x", "Restart it.")
    assert str(requests[0].url) == URL
    assert json.loads(requests[0].content) == {"error_log": "ERROR boom\n  at x", "procedure": "Restart it."}


def test_http_error_status_raises_notification_error():
    with pytest.raises(NotificationError):
        notifier(lambda request: httpx.Response(500)).notify("e", "p")


def test_unreachable_webhook_raises_notification_error():
    def handler(request):
        raise httpx.ConnectError("refused")

    with pytest.raises(NotificationError):
        notifier(handler).notify("e", "p")
