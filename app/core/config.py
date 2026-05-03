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
