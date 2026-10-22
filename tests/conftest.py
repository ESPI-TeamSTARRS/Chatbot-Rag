import os

# notifier_n8n loads the settings at import time: without a .env (CI), collection would fail.
os.environ.setdefault("N8N_WEBHOOK_URL", "http://n8n.test/webhook/x")
os.environ.setdefault("N8N_TOKEN", "test-token")
os.environ.setdefault("LLM_BASE_URL", "http://llm.test/v1")
os.environ.setdefault("LLM_MODEL", "test-model")
os.environ.setdefault("RECIPIENT_EMAIL", "test@example.com")
