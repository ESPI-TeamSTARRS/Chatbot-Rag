FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Applique les correctifs de sécurité Debian publiés depuis la construction de l'image de base
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev

EXPOSE 8000
ENTRYPOINT ["uv", "run", "--no-dev", "chatbot-rag"]
