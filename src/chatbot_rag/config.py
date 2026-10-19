from pathlib import Path

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = Path(Path(__file__).parent, "..", "..", ".env" )


class ConfigError(Exception):
    pass


class Setting(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    DOCS_PATH: Path = Field(
        description="Chemin du dossier de la documentation",
        default=PROJECT_ROOT / "documentations",
    )
    DEBUG: bool = Field(
        description="Active les logs de debug sur la sortie standard",
        default=False,
    )
    LLM_BASE_URL: str = Field(
        description="URL du serveur compatible OpenAI (ex: http://<hote-ollama>:11434/v1)",
    )
    LLM_MODEL: str = Field(
        description="Nom du modèle utilisé (Ollama pour le moment), il doit gérer le tool calling",
    )


def load_setting() -> Setting:
    try:
        return Setting()
    except ValidationError as error:
        names = ", ".join(str(issue["loc"][0]) for issue in error.errors())
        raise ConfigError(f"Missing or invalid environment variable(s): {names}") from error
