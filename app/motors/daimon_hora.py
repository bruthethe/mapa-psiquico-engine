"""
Motor Daimon da Hora (Horas Planetárias Caldeias).

Calcula o regente da hora de nascimento usando o sistema de horas planetárias caldeias.
O período diurno (nascer → pôr do sol) e noturno (pôr → próximo nascer) são divididos
em 12 partes iguais cada. A sequência de regência segue a ordem caldeia:
  Saturno → Júpiter → Marte → Sol → Vênus → Mercúrio → Lua  (repete)

Ponto de partida por dia da semana (hora 1 diurna = nascer do sol):
  Domingo → Sol | Segunda → Lua | Terça → Marte | Quarta → Mercúrio
  Quinta → Júpiter | Sexta → Vênus | Sábado → Saturno
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.core.ephemeris import sunrise, sunset
from app.core.ids import lookup_id
from app.core.temporal import TemporalStatus, TimeInput, local_to_utc, resolve_status

# Ordem caldeia do mais lento para o mais rápido
_CHALDEAN_NAMES: list[str] = [
    "Saturno", "Júpiter", "Marte", "Sol", "Vênus", "Mercúrio", "Lua"
]
_CHALDEAN_IDS: list[int] = [4, 3, 9, 1, 6, 5, 2]

# Índice caldeu do regente da 1ª hora diurna por dia da semana (Python weekday: 0=Seg … 6=Dom)
# Segunda→Lua(6), Terça→Marte(2), Quarta→Mercúrio(5),
# Quinta→Júpiter(1), Sexta→Vênus(4), Sábado→Saturno(0), Domingo→Sol(3)
_WEEKDAY_START_IDX: list[int] = [6, 2, 5, 1, 4, 0, 3]


@dataclass(frozen=True)
class DaimonHoraResult:
    planeta: str           # "Sol", "Lua", "Marte", etc.
    id_gatilho: int        # ID após lookup_id()
    numero_hora: int       # 1–12 (diurna) ou 13–24 (noturna)
    periodo: str           # "diurno" | "noturno"
    status: TemporalStatus
    planeta_b: str | None = None
    id_gatilho_b: int | None = None
    numero_hora_b: int | None = None
    periodo_b: str | None = None


@dataclass
class DaimonHoraMotorResult:
    daimon: DaimonHoraResult
    vote: int
    vote_b: int | None
    overall_status: TemporalStatus


# ── Helpers internos ───────────────────────────────────────────────────────────


def _day_context(
    dt_utc: datetime, birth_date: date, lat: float, lon: float
) -> tuple[datetime, datetime, datetime, int]:
    """
    Retorna (sunrise, sunset, next_sunrise, weekday) do dia planetário que contém dt_utc.

    Se dt_utc cai antes do nascer do sol de birth_date, o nascimento pertence
    à noite do dia anterior (cujo regente define a sequência caldeia).
    """
    sr = sunrise(datetime(birth_date.year, birth_date.month, birth_date.day), lat, lon)

    if dt_utc < sr:
        # Noite do dia anterior
        prev = birth_date - timedelta(days=1)
        prev_sr = sunrise(datetime(prev.year, prev.month, prev.day), lat, lon)
        prev_ss = sunset(datetime(prev.year, prev.month, prev.day), lat, lon)
        return prev_sr, prev_ss, sr, prev.weekday()

    ss = sunset(datetime(birth_date.year, birth_date.month, birth_date.day), lat, lon)
    next_date = birth_date + timedelta(days=1)
    next_sr = sunrise(datetime(next_date.year, next_date.month, next_date.day), lat, lon)
    return sr, ss, next_sr, birth_date.weekday()


def _calc_hora(
    dt_utc: datetime, birth_date: date, lat: float, lon: float
) -> tuple[str, int, int, str]:
    """Retorna (planeta, id, numero_hora 1-24, periodo) para um datetime UTC."""
    sr, ss, next_sr, weekday = _day_context(dt_utc, birth_date, lat, lon)
    start_idx = _WEEKDAY_START_IDX[weekday]

    if sr <= dt_utc < ss:
        day_secs = (ss - sr).total_seconds()
        elapsed = (dt_utc - sr).total_seconds()
        hour_offset = min(int(elapsed / (day_secs / 12)), 11)
        chaldean_idx = (start_idx + hour_offset) % 7
        return (
            _CHALDEAN_NAMES[chaldean_idx],
            lookup_id(_CHALDEAN_IDS[chaldean_idx]),
            hour_offset + 1,
            "diurno",
        )
    else:
        night_secs = (next_sr - ss).total_seconds()
        elapsed = (dt_utc - ss).total_seconds()
        hour_offset = min(int(elapsed / (night_secs / 12)), 11)
        chaldean_idx = (start_idx + 12 + hour_offset) % 7
        return (
            _CHALDEAN_NAMES[chaldean_idx],
            lookup_id(_CHALDEAN_IDS[chaldean_idx]),
            hour_offset + 13,
            "noturno",
        )


# ── Função principal ───────────────────────────────────────────────────────────


def calculate_daimon_hora(
    birth_date: date,
    time_input: TimeInput,
    tz_name: str,
    lat: float,
    lon: float,
) -> DaimonHoraMotorResult:
    """
    Calcula o Daimon da Hora (regente caldeu da hora de nascimento).

    Args:
        birth_date: data de nascimento (horário local)
        time_input: modo temporal — hora de nascimento
        tz_name:    fuso IANA do local de nascimento
        lat:        latitude geográfica (positivo = Norte)
        lon:        longitude geográfica (positivo = Leste)

    Returns:
        DaimonHoraMotorResult com regente da hora.
    """
    dt_a = local_to_utc(datetime.combine(birth_date, time_input.point_a), tz_name)
    dt_b = local_to_utc(datetime.combine(birth_date, time_input.point_b), tz_name)

    planeta_a, id_a, hora_a, periodo_a = _calc_hora(dt_a, birth_date, lat, lon)
    planeta_b, id_b, hora_b, periodo_b = _calc_hora(dt_b, birth_date, lat, lon)

    status = resolve_status(time_input, id_a, id_b)
    hybrid = status == TemporalStatus.HYBRID

    daimon = DaimonHoraResult(
        planeta=planeta_a,
        id_gatilho=id_a,
        numero_hora=hora_a,
        periodo=periodo_a,
        status=status,
        planeta_b=planeta_b if hybrid else None,
        id_gatilho_b=id_b if hybrid else None,
        numero_hora_b=hora_b if hybrid else None,
        periodo_b=periodo_b if hybrid else None,
    )

    return DaimonHoraMotorResult(
        daimon=daimon,
        vote=id_a,
        vote_b=id_b if hybrid else None,
        overall_status=status,
    )
