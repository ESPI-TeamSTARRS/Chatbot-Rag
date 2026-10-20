# Chatbot RAG

HTTP API that takes an error trace, searches the documentation through a BM25 MCP server (the standalone `mcp-server` project, next to this one) and answers with the procedure to follow. It also writes an incident report. Remediation is not executed.

## Configuration

| Variable | Description |
|---|---|
| `DOCS_PATH` | Documentation folder (with Docker: path on the host, mounted at `/app/documentations`) (indexed, `actions-taken/` excluded). Edits, additions and deletions are picked up on the next search, no restart needed |
| `SEARCH_MCP_URL` | URL of the BM25 MCP server (default `http://localhost:8001/mcp`; set automatically by docker compose) |
| `DEBUG` | `true` prints `[DEBUG]` logs on stdout (default `false`) |
| `LLM_BASE_URL` | OpenAI-compatible endpoint (e.g. `http://<ollama-host>:11434/v1`) |
| `LLM_MODEL` | Model name; it must support tool calling |

## Usage

```bash
cp .env.exemple .env      # then edit LLM_BASE_URL and LLM_MODEL
docker compose up --build
```

Docker compose starts two services: `bm25-mcp` (port 8001, see `../mcp-server/README.md`) and the API.

Without Docker: `cd ../mcp-server && uv run bm25-mcp`, then in another terminal `DOCS_PATH=documentations uv run chatbot-rag`. The API listens on port 8000.

```bash
curl -X POST http://localhost:8000/v1/traite-instruction-usager \
  -H 'Content-Type: application/json' \
  -d '{"instruction": "redis.exceptions.TimeoutError: Timeout reading from socket"}'
# {"answer": "...", "report_path": "documentations/actions-taken/<timestamp>-<title>.md"}
```

Status codes: `200` success, `422` missing or blank `instruction`, `502` LLM unreachable or iteration limit reached. More requests are in `http/local-request.http`.

Reports are written to `documentations/actions-taken/<YYYYMMDD-HHMMSS>-<title>.md` (UTC). The title is the name given by the documentation's `Report` section when there is one, otherwise the LLM chooses it; the LLM only provides the title and summary; the error trace and tool calls are added by the application.

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
