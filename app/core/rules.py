import json
from functools import lru_cache

from app.core.config import data_path


@lru_cache(maxsize=1)
def global_rules() -> dict:
    path = data_path() / "engines" / "global-rules.json"
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def rules() -> dict:
    path = data_path() / "engines" / "rules.json"
    return json.loads(path.read_text(encoding="utf-8"))
