"""
Motor Human Design (HD).

Calcula os 13 pontos planetários de Personalidade (nascimento) e Design
(88,736 dias antes), deriva Centros definidos, Tipo Bioenergético,
Autoridade de Decisão e Porta do Sol de Personalidade.
"""

from __future__ import annotations

import json
from collections import defaultdict, deque
from datetime import date, datetime, timedelta
from functools import lru_cache

import swisseph as swe

from app.core.config import data_path, ephemeris_path
from app.core.ids import lookup_id
from app.core.motor_types import HDActivation, HDResult
from app.core.temporal import TemporalStatus, TimeInput, TimeInputType, local_to_utc

# ── Constantes do corpo gráfico HD ────────────────────────────────────────────

# Roda das 64 Portas: índice 0–63, cada posição cobre 5,625° a partir de 0° Áries
_RODA_GATES: list[int] = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42,  3,
    27, 24,  2, 23,  8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56,
    31, 33,  7,  4, 29, 59, 40, 64, 47,  6, 46, 18, 48, 57, 32, 50,
    28, 44,  1, 43, 14, 34,  9,  5, 26, 11, 10, 58, 38, 54, 61, 60,
]

# 36 Canais do corpo gráfico HD (pares de portas de centros adjacentes)
_CHANNELS: list[tuple[int, int]] = [
    # Cabeça ↔ Ajna
    (64, 47), (63,  4), (61, 24),
    # Ajna ↔ Garganta
    (43, 23), (17, 62), (11, 56),
    # Garganta ↔ G Centro
    (33, 13), ( 8,  1), (31,  7), (20, 10),
    # Garganta ↔ Ego
    (45, 21),
    # Garganta ↔ Plexo Solar
    (12, 22), (35, 36),
    # Garganta ↔ Sacral
    (20, 34),
    # Garganta ↔ Baço
    (16, 48), (20, 57),
    # G Centro ↔ Ego
    (25, 51),
    # G Centro ↔ Sacral
    ( 5, 15), (29, 46), ( 2, 14), (10, 34),
    # Ego ↔ Plexo Solar
    (37, 40),
    # Ego ↔ Baço
    (26, 44),
    # Sacral ↔ Plexo Solar
    ( 6, 59),
    # Sacral ↔ Baço
    (27, 50), (34, 57),
    # Sacral ↔ Raiz
    ( 9, 52), ( 3, 60), (42, 53),
    # Plexo Solar ↔ Raiz
    (49, 19), (55, 39), (30, 41),
    # Baço ↔ Raiz
    (18, 58), (28, 38), (32, 54),
]

_MOTORS: frozenset[str] = frozenset({"Sacral", "Plexo_Solar", "Ego", "Raiz"})

# Offset de Design em segundos (88,736 dias)
_DESIGN_OFFSET_S: int = round(88.736 * 86400)

# Planetas HD: (swe_id, nome_pt, derivado?)
# derivado=True → não vai ao ephemeris; calculado a partir de outro
_HD_PLANETS: list[tuple[int, str]] = [
    (swe.SUN,        "sol"),
    (-1,             "terra"),        # = Sol + 180° (derivado)
    (swe.MOON,       "lua"),
    (swe.MEAN_NODE,  "nodo_norte"),
    (-2,             "nodo_sul"),     # = Nodo Norte + 180° (derivado)
    (swe.MERCURY,    "mercurio"),
    (swe.VENUS,      "venus"),
    (swe.MARS,       "marte"),
    (swe.JUPITER,    "jupiter"),
    (swe.SATURN,     "saturno"),
    (swe.URANUS,     "urano"),
    (swe.NEPTUNE,    "netuno"),
    (swe.PLUTO,      "plutao"),
]


# ── Carregamento de dados ──────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def _load_data() -> dict:
    path = data_path() / "chapters-sources" / "data-human-design.json"
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _center_gates() -> dict[str, list[int]]:
    return {
        center: info["portas"]
        for center, info in _load_data()["mapeamento_centros_portas"].items()
        if isinstance(info, dict)
    }


@lru_cache(maxsize=1)
def _gate_center_map() -> dict[int, str]:
    result: dict[int, str] = {}
    for center, gates in _center_gates().items():
        for gate in gates:
            result[gate] = center
    return result


# ── Conversões de longitude ────────────────────────────────────────────────────


def lon_to_gate(lon: float) -> int:
    """Converte longitude eclíptica (0–360°) em Porta HD (1–64)."""
    pos = int(lon / 5.625) % 64
    return _RODA_GATES[pos]


def lon_to_line(lon: float) -> int:
    """Converte longitude eclíptica em Linha HD (1–6) dentro da Porta."""
    frac = (lon % 5.625) / 5.625
    return int(frac * 6) + 1


# ── Cálculo de ativações ───────────────────────────────────────────────────────


def _calc_activations(dt_utc: datetime) -> list[HDActivation]:
    """Calcula 13 ativações planetárias para um momento UTC."""
    swe.set_ephe_path(str(ephemeris_path()))
    hour_frac = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour_frac)

    activations: list[HDActivation] = []
    sol_lon: float = 0.0
    nn_lon: float = 0.0

    for swe_id, name in _HD_PLANETS:
        if swe_id == -1:            # Terra = Sol + 180°
            lon = (sol_lon + 180.0) % 360.0
        elif swe_id == -2:          # Nodo Sul = Nodo Norte + 180°
            lon = (nn_lon + 180.0) % 360.0
        else:
            result, _ = swe.calc_ut(jd, swe_id)
            lon = result[0]
            if swe_id == swe.SUN:
                sol_lon = lon
            elif swe_id == swe.MEAN_NODE:
                nn_lon = lon

        activations.append(HDActivation(
            planeta=name,
            longitude=lon,
            gate=lon_to_gate(lon),
            linha=lon_to_line(lon),
        ))

    return activations


# ── Lógica de centros, canais e tipo ──────────────────────────────────────────


def _defined_centers(active_gates: frozenset[int]) -> frozenset[str]:
    return frozenset(
        center
        for center, gates in _center_gates().items()
        if any(g in active_gates for g in gates)
    )


def _active_channels(active_gates: frozenset[int]) -> list[tuple[int, int]]:
    return [(g1, g2) for g1, g2 in _CHANNELS if g1 in active_gates and g2 in active_gates]


def _reachable_from(start: str, active_gates: frozenset[int]) -> frozenset[str]:
    """Centros alcançáveis via canais ativos a partir de `start`."""
    gc = _gate_center_map()
    adj: dict[str, set[str]] = defaultdict(set)
    for g1, g2 in _CHANNELS:
        if g1 in active_gates and g2 in active_gates:
            c1, c2 = gc.get(g1), gc.get(g2)
            if c1 and c2 and c1 != c2:
                adj[c1].add(c2)
                adj[c2].add(c1)

    visited: set[str] = {start}
    queue: deque[str] = deque([start])
    while queue:
        for neighbor in adj[queue.popleft()] - visited:
            visited.add(neighbor)
            queue.append(neighbor)
    return frozenset(visited)


def _derive_tipo(defined: frozenset[str], active_gates: frozenset[int]) -> str:
    if not defined:
        return "Refletor"
    sacral = "Sacral" in defined
    throat_reachable = _reachable_from("Garganta", active_gates)
    throat_to_motor = bool(throat_reachable & _MOTORS)
    if sacral:
        return "Gerador_Manifestante" if throat_to_motor else "Gerador"
    if "Garganta" in defined and throat_to_motor:
        return "Manifestador"
    return "Projetor"


def _derive_autoridade(defined: frozenset[str], active_gates: frozenset[int]) -> str:
    if "Plexo_Solar" in defined:
        return "Emocional"
    if "Sacral" in defined:
        return "Sacral"
    if "Baco" in defined:
        return "Esplenica"
    if "Ego" in defined:
        ego_reach = _reachable_from("Ego", active_gates)
        return "Ego_Manifest" if "Garganta" in ego_reach else "Ego_Projetado"
    if "G_Centro" in defined:
        return "G_Centro"
    if defined:
        return "Mental"
    return "Lunar"


# ── Snapshot interno ───────────────────────────────────────────────────────────


def _snapshot(dt_birth: datetime) -> dict:
    dt_design = dt_birth - timedelta(seconds=_DESIGN_OFFSET_S)
    pers = _calc_activations(dt_birth)
    desn = _calc_activations(dt_design)
    active = frozenset(a.gate for a in pers + desn)
    defined = _defined_centers(active)
    return {
        "pers": pers,
        "desn": desn,
        "active": active,
        "defined": defined,
        "canais": _active_channels(active),
        "tipo": _derive_tipo(defined, active),
        "autoridade": _derive_autoridade(defined, active),
        "sol_gate": pers[0].gate,   # Sol é sempre o primeiro planeta
    }


# ── Função principal ───────────────────────────────────────────────────────────


def calculate_hd(
    birth_date: date,
    time_input: TimeInput,
    tz_name: str,
) -> HDResult:
    """
    Calcula o perfil Human Design completo.

    Args:
        birth_date: data de nascimento (horário local)
        time_input: modo temporal — hora de nascimento
        tz_name:    fuso IANA do local de nascimento

    Returns:
        HDResult com Tipo, Autoridade, Centros definidos e Porta do Sol de Personalidade.
    """
    dt_a = local_to_utc(datetime.combine(birth_date, time_input.point_a), tz_name)
    dt_b = local_to_utc(datetime.combine(birth_date, time_input.point_b), tz_name)

    snap_a = _snapshot(dt_a)
    snap_b = snap_a if dt_a == dt_b else _snapshot(dt_b)

    tipo_a, tipo_b = snap_a["tipo"], snap_b["tipo"]
    sol_a, sol_b   = snap_a["sol_gate"], snap_b["sol_gate"]

    if time_input.type == TimeInputType.EXACT:
        status = TemporalStatus.EXACT
    elif tipo_a == tipo_b and sol_a == sol_b:
        status = TemporalStatus.SAFE
    else:
        status = TemporalStatus.HYBRID

    hybrid = status == TemporalStatus.HYBRID
    master = _load_data()["data_master_design"]
    tipo_data = master["tipos_bioenergeticos"]
    aut_data  = master["autoridades_decisao"]

    tipo_id  = lookup_id(tipo_data[tipo_a]["id_gatilho"])
    aut_id   = lookup_id(aut_data[snap_a["autoridade"]]["id_gatilho"])

    return HDResult(
        personalidade=snap_a["pers"],
        design=snap_a["desn"],
        centros_definidos=snap_a["defined"],
        canais_ativos=snap_a["canais"],
        tipo=tipo_a,
        estrategia=tipo_data[tipo_a]["estrategia"],
        tipo_id_gatilho=tipo_id,
        autoridade=snap_a["autoridade"],
        autoridade_id_gatilho=aut_id,
        porta_sol_personalidade=sol_a,
        vote=tipo_id,
        overall_status=status,
        tipo_b=tipo_b if hybrid else None,
        estrategia_b=tipo_data[tipo_b]["estrategia"] if hybrid else None,
        tipo_b_id_gatilho=lookup_id(tipo_data[tipo_b]["id_gatilho"]) if hybrid else None,
        porta_sol_personalidade_b=sol_b if hybrid and sol_a != sol_b else None,
    )
