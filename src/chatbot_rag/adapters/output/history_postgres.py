from datetime import datetime

import psycopg

from chatbot_rag.domain import HistoryError
from chatbot_rag.ports import RequestHistoryPort

CONNECT_TIMEOUT = 3
SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    path TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS requests (
    id SERIAL PRIMARY KEY,
    received_at TIMESTAMPTZ NOT NULL,
    content TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS request_documents (
    request_id INTEGER NOT NULL REFERENCES requests(id),
    document_id INTEGER NOT NULL REFERENCES documents(id),
    PRIMARY KEY (request_id, document_id)
);
"""


class PostgresRequestHistory(RequestHistoryPort):
    """Stores each request (arrival time, content) and the documents it used in PostgreSQL."""

    def __init__(self, url: str):
        self._url = url
        self._schema_ready = False

    def record_request(self, received_at: datetime, content: str) -> int:
        def insert(connection: psycopg.Connection) -> int:
            row = connection.execute(
                "INSERT INTO requests (received_at, content) VALUES (%s, %s) RETURNING id",
                (received_at, content),
            ).fetchone()
            return row[0]

        return self._run(insert)

    def record_documents(self, request_id: int, paths: list[str]) -> None:
        def insert(connection: psycopg.Connection) -> None:
            for path in dict.fromkeys(paths):
                document_id = connection.execute(
                    "INSERT INTO documents (path) VALUES (%s) "
                    "ON CONFLICT (path) DO UPDATE SET path = EXCLUDED.path RETURNING id",
                    (path,),
                ).fetchone()[0]
                connection.execute(
                    "INSERT INTO request_documents (request_id, document_id) VALUES (%s, %s) "
                    "ON CONFLICT DO NOTHING",
                    (request_id, document_id),
                )

        self._run(insert)

    def _run(self, action):
        try:
            with psycopg.connect(self._url, connect_timeout=CONNECT_TIMEOUT) as connection:
                if not self._schema_ready:
                    connection.execute(SCHEMA)
                    self._schema_ready = True
                return action(connection)
        except psycopg.Error as error:
            raise HistoryError(f"History database error: {error}") from error
