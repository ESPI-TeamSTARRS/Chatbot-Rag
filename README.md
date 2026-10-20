# Chatbot RAG

HTTP API that takes an error trace, searches the documentation through a BM25 MCP server (the standalone `mcp-server` project, next to this one) and answers with the procedure to follow. The error log and the procedure are then sent, as is, to an n8n webhook.

## Configuration

| Variable | Description |
|---|---|
| `DOCS_PATH` | Documentation folder (with Docker: path on the host, mounted at `/app/documentations`) (indexed, `actions-taken/` excluded). Edits, additions and deletions are picked up on the next search, no restart needed |
| `SEARCH_MCP_URL` | URL of the BM25 MCP server (default `http://localhost:8001/mcp`; set automatically by docker compose) |
| `LOKI_URL` | Loki receiving the request history (default `http://localhost:3100`; docker compose defaults to its `loki` service, which only exists with `--profile dev`) |
| `DEBUG` | `true` prints `[DEBUG]` logs on stdout (default `false`) |
| `N8N_WEBHOOK_URL` | n8n webhook receiving a JSON POST `{"error_log": ..., "procedure": ...}` (the request received and the answer, unchanged) |
| `LLM_BASE_URL` | OpenAI-compatible endpoint (e.g. `http://<ollama-host>:11434/v1`) |
| `LLM_MODEL` | Model name; it must support tool calling |

## Request history (Loki)

Each request is pushed to Loki as log lines, labelled `app="chatbot-rag"`: `event="request"` (line timestamp = arrival time, JSON `{request_id, content}`) and `event="document_used"` (one line per document returned by a search, JSON `{request_id, path}`). The list of documents is therefore always up to date: `sum by (path) (count_over_time({app="chatbot-rag", event="document_used"} | json [30d]))`. The history never breaks a diagnosis: if Loki is down, a `[WARNING]` is printed on stdout and the diagnosis goes on.

The `loki` service of the docker compose belongs to the `dev` profile: `docker compose up -d` does not start it (use the Loki that already exists and set `LOKI_URL`), `docker compose --profile dev up -d` starts it on port 3100.

## Usage

```bash
cp .env.exemple .env      # then edit LLM_BASE_URL, LLM_MODEL and N8N_WEBHOOK_URL
docker compose up --build
```

Docker compose starts two services: `bm25-mcp` (port 8001, see `../mcp-server/README.md`) and the API.

Without Docker: `cd ../mcp-server && uv run bm25-mcp`, then in another terminal `DOCS_PATH=documentations uv run chatbot-rag`. The API listens on port 8000.

```bash
curl -X POST http://localhost:8000/v1/traite-instruction-usager \
  -H 'Content-Type: application/json' \
  -d '{"instruction": "redis.exceptions.TimeoutError: Timeout reading from socket"}'
# {"answer": "..."}
```

Status codes: `200` success, `422` missing or blank `instruction`, `502` LLM unreachable or iteration limit reached. More requests are in `http/local-request.http`.

The webhook call never breaks a diagnosis: if n8n is unreachable, a `[WARNING]` is printed and the answer is still returned.

## Développement

Les tâches sont lancées avec [Poe the Poet](https://poethepoet.natn.io/) via uv : `uv run poe <tâche>` (`uv run poe --help` les liste).

| Commande | Description |
|---|---|
| `uv run poe serve` | Démarre l'API sur le port 8000 (nécessite `LLM_BASE_URL`, `LLM_MODEL` et le serveur MCP de recherche) |
| `uv run poe test` | Tous les tests |
| `uv run poe test-tu` | Tests unitaires (`tests/tu`, fakes uniquement) |
| `uv run poe test-ti` | Tests d'intégration (`tests/ti`, vrai système de fichiers et faux serveur MCP) |
| `uv run poe check` | Toutes les vérifications (pour l'instant les tests), appelée par le hook `pre-push` |

Le serveur MCP a ses propres tests : `cd ../mcp-server && uv run pytest`.

## Git hooks

```bash
git config core.hooksPath "git-hooks"
```
