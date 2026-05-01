import os
from pathlib import Path

# Define DATA_PATH antes de qualquer import de módulos que usem lru_cache nos loaders.
# Aponta para data/ na raiz do monorepo (backend/../data).
os.environ.setdefault(
    "DATA_PATH",
    str(Path(__file__).parent.parent / "data"),
)
