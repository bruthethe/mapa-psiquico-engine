"""Motor Ba Zi (Astrologia Chinesa) — calcula os Quatro Pilares e retorna IDs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, time
from functools import lru_cache

import swisseph as swe

from app.core.config import data_path
from app.core.ephemeris import Planet, tropical_longitude
from app.core.ids import lookup_id
from app.core.temporal import TemporalStatus, TimeInput, local_to_utc, resolve_status

# 12 Ramos Terrestres (地支): índice 0=子(Rato) … 11=亥(Porco)
_ANIMALS: list[str] = [
    "rato", "boi", "tigre", "coelho", "dragao", "serpente",
    "cavalo", "cabra", "macaco", "galo", "cao", "porco",
]

# 10 Troncos Celestiais (天干): elemento por stem index (0=甲 … 9=癸)
_STEM_ELEMENTS: list[str] = [
    "madeira", "madeira",  # 甲, 乙
    "fogo",    "fogo",     # 丙, 丁
    "terra",   "terra",    # 戊, 己
    "metal",   "metal",    # 庚, 辛
    "agua",    "agua",     # 壬, 癸
]

# 五虎遁年起月法: year_stem % 5 → stem index do Mês Tigre (início do ciclo mensal)
# 甲/己→丙(2), 乙/庚→戊(4), 丙/辛→庚(6), 丁/壬→壬(8), 戊/癸→甲(0)
_MONTH_STEM_START: list[int] = [2, 4, 6, 8, 0]

# 五鼠遁日起時法: day_stem % 5 → stem index da Hora Rato (início do ciclo horário)
# 甲/己→甲(0), 乙/庚→丙(2), 丙/辛→戊(4), 丁/壬→庚(6), 戊/癸→壬(8)
_HOUR_STEM_START: list[int] = [0, 2, 4, 6, 8]

# Longitude solar tropical que marca Li Chun (立春) — início do ano Ba Zi
_LI_CHUN_LON: float = 315.0


@lru_cache(maxsize=1)
def _load_data() -> dict:
    path = data_path() / "chapters-sources" / "data-chinese.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _raw_id(animal: str) -> int:
    """Retorna o ID configurado para um animal."""
    return _load_data()["data_master_bazi"]["mapeamento_de_saida"][animal]["id_gatilho"]


def _hour_branch(hour: int) -> int:
    """Converte hora do dia (0–23) em branch index (0–11)."""
    return (hour + 1) // 2 % 12


def _calc_hour_stem(day_stem_idx: int, hour_branch_idx: int) -> int:
    """Stem index do Pilar da Hora (五鼠遁日起時法)."""
    rato_start = _HOUR_STEM_START[day_stem_idx % 5]
    return (rato_start + hour_branch_idx) % 10


# ── Dataclasses de resultado ───────────────────────────────────────────────────


@dataclass(frozen=True)
class BaZiPillar:
    animal: str      # "rato", "boi", "tigre", ..., "porco"
    elemento: str    # "madeira", "fogo", "terra", "metal", "agua"
    id_gatilho: int


@dataclass(frozen=True)
class BaZiPilarHora:
    """Pilar da Hora."""
    animal: str
    elemento: str
    id_gatilho: int
    status: TemporalStatus
    animal_b: str | None = None
    elemento_b: str | None = None
    id_gatilho_b: int | None = None


@dataclass
class BaZiResult:
    ano: BaZiPillar
    mes: BaZiPillar
    dia: BaZiPillar
    hora: BaZiPilarHora
    vote: int
    overall_status: TemporalStatus


# ── Cálculo de cada pilar ──────────────────────────────────────────────────────


def _calc_year_pillar(birth_date: date, sun_lon: float) -> tuple[BaZiPillar, int]:
    """
    Pilar do Ano ajustado para Li Chun (Sol = 315°).
    Nascimentos em jan–fev antes de Li Chun pertencem ao ano Ba Zi anterior.
    Retorna (BaZiPillar, year_stem_idx).
    """
    year = birth_date.year
    if birth_date.month <= 2 and sun_lon < _LI_CHUN_LON:
        year -= 1
    branch_idx = (year - 4) % 12
    stem_idx = (year - 4) % 10
    animal = _ANIMALS[branch_idx]
    return BaZiPillar(
        animal=animal,
        elemento=_STEM_ELEMENTS[stem_idx],
        id_gatilho=lookup_id(_raw_id(animal)),
    ), stem_idx


def _calc_month_pillar(sun_lon: float, year_stem_idx: int) -> BaZiPillar:
    """
    Pilar do Mês determinado pela longitude solar tropical.
    Li Chun (315°) inicia o Mês Tigre (sequência Ba Zi mês 0).
    """
    shifted = (sun_lon - _LI_CHUN_LON + 360) % 360
    month_seq_idx = int(shifted / 30)
    branch_idx = (month_seq_idx + 2) % 12
    stem_idx = (_MONTH_STEM_START[year_stem_idx % 5] + month_seq_idx) % 10
    animal = _ANIMALS[branch_idx]
    return BaZiPillar(
        animal=animal,
        elemento=_STEM_ELEMENTS[stem_idx],
        id_gatilho=lookup_id(_raw_id(animal)),
    )


def _calc_day_pillar(birth_date: date) -> tuple[BaZiPillar, int]:
    """
    Pilar do Dia via ciclo de 60 dias (Julian Day Number).
    Referência: 2000-01-01 ao meio-dia = 甲戌日 (stem 0 = madeira, branch 10 = cão).
    Retorna (BaZiPillar, day_stem_idx) — stem_idx necessário para o Pilar da Hora.
    """
    jdn = round(swe.julday(birth_date.year, birth_date.month, birth_date.day, 12.0))
    stem_idx = (jdn + 5) % 10
    branch_idx = (jdn + 5) % 12
    animal = _ANIMALS[branch_idx]
    return BaZiPillar(
        animal=animal,
        elemento=_STEM_ELEMENTS[stem_idx],
        id_gatilho=lookup_id(_raw_id(animal)),
    ), stem_idx


def _hora_from_time(t: time, day_stem_idx: int) -> tuple[str, str, int]:
    """Calcula (animal, elemento, id_gatilho) do Pilar da Hora para um dado horário."""
    branch_idx = _hour_branch(t.hour)
    stem_idx = _calc_hour_stem(day_stem_idx, branch_idx)
    animal = _ANIMALS[branch_idx]
    return animal, _STEM_ELEMENTS[stem_idx], lookup_id(_raw_id(animal))


# ── Função principal ───────────────────────────────────────────────────────────


def calculate_bazi(
    birth_date: date,
    time_input: TimeInput,
    tz_name: str,
) -> BaZiResult:
    """
    Calcula os Quatro Pilares Ba Zi e converte em IDs.

    Args:
        birth_date: data de nascimento (horário local)
        time_input: modo temporal — hora de nascimento
        tz_name:    fuso IANA do local de nascimento

    Returns:
        BaZiResult com os quatro pilares.
    """
    dt_a = local_to_utc(datetime.combine(birth_date, time_input.point_a), tz_name)
    sun_lon = tropical_longitude(Planet.SUN, dt_a).longitude

    ano, year_stem_idx = _calc_year_pillar(birth_date, sun_lon)
    mes = _calc_month_pillar(sun_lon, year_stem_idx)
    dia, day_stem_idx = _calc_day_pillar(birth_date)

    animal_a, elem_a, id_a = _hora_from_time(time_input.point_a, day_stem_idx)
    animal_b, elem_b, id_b = _hora_from_time(time_input.point_b, day_stem_idx)

    hora_status = resolve_status(time_input, id_a, id_b)
    hybrid = hora_status == TemporalStatus.HYBRID

    hora = BaZiPilarHora(
        animal=animal_a,
        elemento=elem_a,
        id_gatilho=id_a,
        status=hora_status,
        animal_b=animal_b if hybrid else None,
        elemento_b=elem_b if hybrid else None,
        id_gatilho_b=id_b if hybrid else None,
    )

    return BaZiResult(
        ano=ano,
        mes=mes,
        dia=dia,
        hora=hora,
        vote=dia.id_gatilho,
        overall_status=hora_status,
    )
