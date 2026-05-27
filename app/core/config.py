import os
from pathlib import Path


def data_path() -> Path:
    """Resolve o caminho base para os dados da aplicação."""
    env = os.getenv("DATA_PATH")
    if not env:
        raise RuntimeError("DATA_PATH environment variable is not set.")
    return Path(env)


def ephemeris_path() -> Path:
    """Caminho para os arquivos .se1 do Swiss Ephemeris."""
    return data_path() / "ephemeris"


def frontend_url() -> str:
    """URL base do frontend — usada pelo endpoint PDF para abrir /report/:id."""
    return os.getenv("FRONTEND_URL", "http://localhost:3000")
