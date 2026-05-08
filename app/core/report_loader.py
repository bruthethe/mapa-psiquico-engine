"""
Report data loader — loads and indexes all ID-indexed JSON files at startup.

Covers (25 files total):
  Nível 2 (translations/): 14 panteões + sombra-goetia
  Nível 2 (chapters-sources/): data-mapa-arquétipos.json
  Nível 3 (materialization/): 8 sensorial files

ID resolution applied automatically on every lookup:
  8  → 4  (Oitava Superior — no master label)
  22 → 4  (Mestre Construtor — master label applied)
  11, 33  → own data + master label applied
"""

from __future__ import annotations

import json
import unicodedata
from functools import lru_cache
from typing import Any

from app.core.config import data_path
from app.core.ids import MasterLabel, get_master_label, lookup_id

# IDs present as keys in the JSON files (8 and 22 are absent; they redirect to 4)
DATA_IDS: frozenset[int] = frozenset({1, 2, 3, 4, 5, 6, 7, 9, 11, 33})


def _key(stem: str) -> str:
    """Normalize filename stem to ASCII for consistent source keys."""
    return unicodedata.normalize("NFD", stem).encode("ascii", "ignore").decode()


@lru_cache(maxsize=1)
def _index() -> dict[str, dict[int, Any]]:
    """
    Loads all ID-indexed JSON files and builds an in-memory index.
    Returns: source_key → {int_id: value}
    """
    root = data_path()
    idx: dict[str, dict[int, Any]] = {}

    for path in sorted((root / "translations").iterdir()):
        if path.suffix != ".json":
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        idx[_key(path.stem)] = {int(k): v for k, v in raw["mapeamento"].items()}

    for path in sorted((root / "materialization").iterdir()):
        if path.suffix != ".json":
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        idx[_key(path.stem)] = {int(k): v for k, v in raw["mapeamento"].items()}

    arq = root / "chapters-sources" / "data-mapa-arquétipos.json"
    raw = json.loads(arq.read_text(encoding="utf-8"))
    idx[_key(arq.stem)] = {int(k): v for k, v in raw["matriz"].items()}

    return idx


def sources() -> frozenset[str]:
    """Returns the set of all loaded source keys."""
    return frozenset(_index().keys())


def lookup(source: str, id_: int) -> Any:
    """
    Returns data for the given ID from the specified source.
    Automatically resolves 8 → 4 and 22 → 4 before the lookup.
    """
    return _index()[source][lookup_id(id_)]


def lookup_with_label(source: str, id_: int) -> tuple[Any, MasterLabel | None]:
    """Same as lookup, and also returns the master label for IDs 11, 22, 33."""
    return lookup(source, id_), get_master_label(id_)
