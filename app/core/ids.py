from dataclasses import dataclass

from app.core.rules import global_rules

# IDs válidos do sistema
VALID_IDS: frozenset[int] = frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33})

# Nunca reduzidos durante cálculos intermediários
MASTER_NUMBERS: frozenset[int] = frozenset({11, 22, 33})

# Redirecionamentos de ID
_LOOKUP_OVERRIDES: dict[int, int] = {8: 4, 22: 4}


def theosophic_reduce(n: int) -> int:
    """Reduz n teosoficamente até 1–9, preservando 11, 22 e 33."""
    if n < 0:
        raise ValueError(f"Redução teosófica não opera em negativos: {n}")
    while n > 9 and n not in MASTER_NUMBERS:
        n = sum(int(d) for d in str(n))
    return n


def lookup_id(id_: int) -> int:
    """Retorna o ID a usar para consulta de dados, aplicando redirecionamentos configurados."""
    return _LOOKUP_OVERRIDES.get(id_, id_)


@dataclass(frozen=True)
class MasterLabel:
    id_dados: int
    titulo: str
    texto: str


def get_master_label(id_: int) -> MasterLabel | None:
    """Retorna o label especial para 11, 22 ou 33. None para demais IDs."""
    entry = global_rules().get("labels_mestres", {}).get(str(id_))
    if entry is None:
        return None
    return MasterLabel(
        id_dados=entry["id_dados"],
        titulo=entry["titulo"],
        texto=entry["texto"],
    )
