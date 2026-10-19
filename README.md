# Chatbot RAG

HTTP API that takes an error trace, searches the documentation with BM25 and answers with the procedure to follow. It also writes an incident report. Remediation is not executed.

## Configuration

| Variable | Description |
|---|---|
| `DOCS_PATH` | Documentation folder (with Docker: path on the host, mounted at `/app/documentations`) (indexed, `actions-taken/` excluded). Edits, additions and deletions are picked up on the next search, no restart needed |
| `DEBUG` | `true` prints `[DEBUG]` logs on stdout (default `false`) |
| `LLM_BASE_URL` | OpenAI-compatible endpoint (e.g. `http://<ollama-host>:11434/v1`) |
| `LLM_MODEL` | Model name; it must support tool calling |

## Usage

```bash
cp .env.exemple .env      # then edit LLM_BASE_URL and LLM_MODEL
docker compose up --build
```

Without Docker: `DOCS_PATH=documentations uv run chatbot-rag`. The API listens on port 8000.

```bash
curl -X POST http://localhost:8000/v1/traite-instruction-usager \
  -H 'Content-Type: application/json' \
  -d '{"instruction": "redis.exceptions.TimeoutError: Timeout reading from socket"}'
# {"answer": "...", "report_path": "documentations/actions-taken/<timestamp>-<title>.md"}
```

Status codes: `200` success, `422` missing or blank `instruction`, `502` LLM unreachable or iteration limit reached. More requests are in `http/local-request.http`.

Reports are written to `documentations/actions-taken/<YYYYMMDD-HHMMSS>-<title>.md` (UTC). The title is the name given by the documentation's `Report` section when there is one, otherwise the LLM chooses it; the LLM only provides the title and summary; the error trace and tool calls are added by the application.

## Tests

Tests are split by level: `tests/tu` (unit, fakes only) and `tests/ti` (integration, real filesystem).

```bash
uv run pytest            # everything
uv run pytest tests/tu   # or tests/ti
```

## Git hooks

```bash
git config core.hooksPath "git-hooks"
```
