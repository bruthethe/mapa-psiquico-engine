import zoneinfo
from dataclasses import dataclass
from datetime import datetime, time, timezone
from enum import Enum


class TimeInputType(str, Enum):
    EXACT = "exact"      # Caminho A — hora e minuto exatos
    WINDOW = "window"    # Caminho B — janela de 4 horas
    UNKNOWN = "unknown"  # Caminho C — hora desconhecida (fallback 12:00)


class TimeWindow(str, Enum):
    MADRUGADA = "madrugada"      # 00:00 – 03:59
    MANHA_CEDO = "manha_cedo"   # 04:00 – 07:59
    MANHA = "manha"              # 08:00 – 11:59
    TARDE = "tarde"              # 12:00 – 15:59
    FINAL_TARDE = "final_tarde"  # 16:00 – 19:59
    NOITE = "noite"              # 20:00 – 23:59


class TemporalStatus(int, Enum):
    HYBRID = 1  # Frequência em Transição — A ≠ B (cúspide ou conflito de janela)
    SAFE = 2    # Frequência Definida — janela validada ou fallback sem cúspide
    EXACT = 3   # Fidelidade Total — hora exata informada


_FALLBACK = time(12, 0)

_WINDOW_BOUNDS: dict[TimeWindow, tuple[time, time]] = {
    TimeWindow.MADRUGADA:   (time(0, 0),  time(3, 59)),
    TimeWindow.MANHA_CEDO:  (time(4, 0),  time(7, 59)),
    TimeWindow.MANHA:       (time(8, 0),  time(11, 59)),
    TimeWindow.TARDE:       (time(12, 0), time(15, 59)),
    TimeWindow.FINAL_TARDE: (time(16, 0), time(19, 59)),
    TimeWindow.NOITE:       (time(20, 0), time(23, 59)),
}


@dataclass(frozen=True)
class TimeInput:
    type: TimeInputType
    point_a: time  # Ponto de teste A (início da janela ou hora exata)
    point_b: time  # Ponto de teste B (fim da janela ou hora exata)


def parse_time_input(
    exact_time: time | None = None,
    window: TimeWindow | None = None,
) -> TimeInput:
    """Classifica o input de hora em um dos 3 caminhos temporais e retorna os pontos de teste."""
    if exact_time is not None:
        return TimeInput(type=TimeInputType.EXACT, point_a=exact_time, point_b=exact_time)

    if window is not None:
        point_a, point_b = _WINDOW_BOUNDS[window]
        return TimeInput(type=TimeInputType.WINDOW, point_a=point_a, point_b=point_b)

    return TimeInput(type=TimeInputType.UNKNOWN, point_a=_FALLBACK, point_b=_FALLBACK)


def local_to_utc(dt: datetime, tz_name: str) -> datetime:
    """
    Converte um datetime local sem fuso (naive) para UTC (naive).

    Args:
        dt: datetime local sem timezone (ex: 1990-05-15 14:30)
        tz_name: nome IANA do fuso (ex: "America/Sao_Paulo"), retornado pelo geocoding

    Returns:
        datetime em UTC sem timezone (naive), pronto para o Swiss Ephemeris.

    Exemplo:
        local_to_utc(datetime(1990, 5, 15, 14, 30), "America/Sao_Paulo")
        → datetime(1990, 5, 15, 17, 30)  # BRT = UTC-3
    """
    tz = zoneinfo.ZoneInfo(tz_name)
    local_aware = dt.replace(tzinfo=tz)
    utc_aware = local_aware.astimezone(timezone.utc)
    return utc_aware.replace(tzinfo=None)


def resolve_status(time_input: TimeInput, id_a: int, id_b: int) -> TemporalStatus:
    """
    Determina o status temporal a partir dos IDs produzidos pelos dois pontos de teste.

    Chamado por cada motor após calcular id_a (de point_a) e id_b (de point_b).
    Para Caminho C, cúspide é sinalizada pelo motor passando id_a ≠ id_b.
    """
    if time_input.type == TimeInputType.EXACT:
        return TemporalStatus.EXACT
    if id_a == id_b:
        return TemporalStatus.SAFE
    return TemporalStatus.HYBRID
