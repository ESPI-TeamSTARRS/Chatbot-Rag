import os
from datetime import datetime, timezone

import psycopg
import pytest

from chatbot_rag.adapters.output.history_postgres import PostgresRequestHistory

URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_DATABASE_URL not set")


def test_requests_and_new_documents_are_stored():
    history = PostgresRequestHistory(URL)
    request_id = history.record_request(datetime(2026, 10, 20, tzinfo=timezone.utc), "ERROR boom")
    history.record_documents(request_id, ["errors-cases/a.md", "errors-cases/a.md", "errors-cases/b.md"])
    history.record_documents(request_id, ["errors-cases/a.md"])
    with psycopg.connect(URL) as connection:
        assert connection.execute("SELECT content FROM requests WHERE id = %s", (request_id,)).fetchone() == ("ERROR boom",)
        assert connection.execute(
            "SELECT count(*) FROM request_documents WHERE request_id = %s", (request_id,)
        ).fetchone() == (2,)
        assert connection.execute("SELECT count(*) FROM documents WHERE path = 'errors-cases/a.md'").fetchone() == (1,)
