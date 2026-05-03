import os
from pathlib import Path

# Carrega .env local se existir (não versionado — apenas para desenvolvimento local).
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            _val = _v.strip()
            # Resolve paths relativos em relação ao diretório do .env
            if _val and not os.path.isabs(_val):
                _val = str((_env_file.parent / _val).resolve())
            os.environ.setdefault(_k.strip(), _val)

# Define DATA_PATH antes de qualquer import de módulos que usem lru_cache nos loaders.
os.environ.setdefault("DATA_PATH", "")
