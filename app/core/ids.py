from dataclasses import dataclass

from app.core.rules import global_rules

# IDs que existem como arquétipos autônomos no sistema
VALID_IDS: frozenset[int] = frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33})

# Nunca reduzidos durante cálculos intermediários
MASTER_NUMBERS: frozenset[int] = frozenset({11, 22, 33})

# IDs que usam dados de outro ID nos Níveis 2 e 3
_LOOKUP_OVERRIDES: dict[int, int] = {8: 4, 22: 4}


def theosophic_reduce(n: int) -> int:
    """
    Reduz n teosoficamente até 1–9, parando em números mestres (11, 22, 33).

    Exemplos:
        29  → 11   (2+9=11, mestre — para)
        44  → 8    (4+4=8)
        33  → 33   (mestre — para imediatamente)
        100 → 1    (1+0+0=1)
    """
    if n < 0:
        raise ValueError(f"Redução teosófica não opera em negativos: {n}")
    while n > 9 and n not in MASTER_NUMBERS:
        n = sum(int(d) for d in str(n))
    return n


def lookup_id(id_: int) -> int:
    """
    Retorna o ID a usar para consultas nos Níveis 2 e 3.

    Aplica a Regra da Oitava Superior (8→4) e o redirecionamento do 22→4.
    IDs comuns retornam a si mesmos.
    """
    return _LOOKUP_OVERRIDES.get(id_, id_)


@dataclass(frozen=True)
class MasterLabel:
    id_dados: int
    titulo: str
    texto: str


def get_master_label(id_: int) -> MasterLabel | None:
    """
    Retorna o label de número mestre para 11, 22 ou 33. None para IDs comuns.

    O label é exibido no início do capítulo antes dos dados do id_dados.
    """
    entry = global_rules().get("labels_mestres", {}).get(str(id_))
    if entry is None:
        return None
    return MasterLabel(
        id_dados=entry["id_dados"],
        titulo=entry["titulo"],
        texto=entry["texto"],
    )
