import json

import httpx
import pytest

from chatbot_rag.adapters.output.notifier_n8n import N8nWebhookNotifier
from chatbot_rag.domain import NotificationError

URL = "http://n8n/webhook/incident"


def notifier(handler):
    return N8nWebhookNotifier(URL, httpx.Client(transport=httpx.MockTransport(handler)))


def test_posts_email_with_error_log_and_procedure():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200)

    notifier(handler).notify("ERROR boom\n  at x", "Restart it.")
    assert str(requests[0].url) == URL
    payload = json.loads(requests[0].content)
    assert payload["subject"] == "[RAG] Erreurs détectées"
    assert "<pre>ERROR boom\n  at x</pre>" in payload["body"]
    assert "<p>Restart it.</p>" in payload["body"]


def test_http_error_status_raises_notification_error():
    with pytest.raises(NotificationError):
        notifier(lambda request: httpx.Response(500)).notify("e", "p")


def test_unreachable_webhook_raises_notification_error():
    def handler(request):
        raise httpx.ConnectError("refused")

    with pytest.raises(NotificationError):
        notifier(handler).notify("e", "p")


def test_check_available_accepts_any_http_status():
    for status in (200, 404, 405, 500):
        notifier(lambda request, status=status: httpx.Response(status)).check_available()


def test_check_available_raises_when_n8n_is_unreachable():
    def handler(request):
        raise httpx.ConnectError("refused")

    with pytest.raises(NotificationError):
        notifier(handler).check_available()


def test_email_body_renders_procedure_markdown_as_html():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200)

    notifier(handler).notify("ERROR <boom>", "## Étapes\n\n1. **Restart** it\n2. <script>x</script>")
    body = json.loads(requests[0].content)["body"]
    assert "<h2>Étapes</h2>" in body
    assert "<ol>" in body and "<strong>Restart</strong>" in body
    assert "<script>" not in body
    assert "<pre>ERROR &lt;boom&gt;</pre>" in body
