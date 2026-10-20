import re
from pathlib import Path

import pytest

from chatbot_rag.config import ConfigError, Setting, load_setting

SRC = Path(__file__).parents[2] / "src" / "chatbot_rag"


def test_setting_reads_uppercase_environment_variables(monkeypatch):
    monkeypatch.setitem(Setting.model_config, "env_file", None)
    monkeypatch.setenv("DOCS_PATH", "/d")
    monkeypatch.setenv("LLM_BASE_URL", "http://h/v1")
    monkeypatch.setenv("N8N_WEBHOOK_URL", "http://n/w")
    monkeypatch.setenv("LLM_MODEL", "m")
    setting = Setting()
    assert (str(setting.DOCS_PATH), setting.LLM_BASE_URL, setting.LLM_MODEL) == ("/d", "http://h/v1", "m")


def test_missing_variable_is_named(monkeypatch):
    monkeypatch.setitem(Setting.model_config, "env_file", None)
    monkeypatch.setenv("DOCS_PATH", "/d")
    monkeypatch.setenv("LLM_BASE_URL", "http://h/v1")
    monkeypatch.setenv("N8N_WEBHOOK_URL", "http://n/w")
    monkeypatch.delenv("LLM_MODEL", raising=False)
    with pytest.raises(ConfigError, match="LLM_MODEL"):
        load_setting()


@pytest.mark.parametrize("layer", ["domain", "ports", "usecases"])
def test_inner_layers_do_not_import_adapters(layer):
    for file in (SRC / layer).glob("*.py"):
        assert not re.search(r"chatbot_rag\.adapters|import adapters", file.read_text()), file


def test_env_file_is_two_levels_above_config_py(tmp_path, monkeypatch):
    from chatbot_rag import config

    assert (config.ENV_FILE.parent.resolve() == Path(config.__file__).parents[2])
    env_file = tmp_path / ".env"
    env_file.write_text("LLM_BASE_URL=http://f/v1\nLLM_MODEL=from-file\nN8N_WEBHOOK_URL=http://n/w\n")
    for name in ("LLM_BASE_URL", "LLM_MODEL", "DOCS_PATH", "N8N_WEBHOOK_URL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setitem(Setting.model_config, "env_file", env_file)
    assert Setting().LLM_MODEL == "from-file"
