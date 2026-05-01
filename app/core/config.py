import os
from pathlib import Path


def data_path() -> Path:
    """Resolve o caminho base para a pasta data/ via DATA_PATH (env var) ou convenção do monorepo."""
    env = os.getenv("DATA_PATH")
    if env:
        return Path(env)
    return Path(__file__).parent.parent.parent.parent / "data"


def ephemeris_path() -> Path:
    """Caminho para os arquivos .se1 do Swiss Ephemeris."""
    return data_path() / "ephemeris"
