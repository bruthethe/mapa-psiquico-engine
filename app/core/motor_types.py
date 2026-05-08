"""
Result dataclasses for ephemeris-based motors (tropical, vedica, human_design).

Kept in a separate module so chapter assemblers and tests can import
the types without triggering the transitive swisseph dependency.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.temporal import TemporalStatus


@dataclass(frozen=True)
class PlanetResult:
    planet: str           # chave PT: "sol", "lua", "marte", etc.
    sign: str             # chave PT do signo em point_a
    id_gatilho: int
    status: TemporalStatus
    sign_b: str | None = None
    id_gatilho_b: int | None = None


@dataclass
class TropicalResult:
    sol: PlanetResult
    lua: PlanetResult
    ascendente: PlanetResult | None
    planets: list[PlanetResult]
    vote: int
    vote_b: int | None
    overall_status: TemporalStatus


@dataclass(frozen=True)
class NakshatraResult:
    index: int           # 0–26
    nome: str
    id_gatilho: int
    regente: str
    pada: int            # 1–4
    purushartha: str
    simbolo: str
    deidade: str
    qualidade: str
    status: TemporalStatus
    nome_b: str | None = None
    id_gatilho_b: int | None = None
    pada_b: int | None = None


@dataclass(frozen=True)
class AtmakarakaResult:
    graha: str
    id_gatilho: int
    grau_no_signo: float


@dataclass
class VedicaResult:
    nakshatra: NakshatraResult
    atmakaraka: AtmakarakaResult
    vote: int
    vote_b: int | None
    overall_status: TemporalStatus


@dataclass(frozen=True)
class BaZiPillar:
    animal: str
    elemento: str
    id_gatilho: int


@dataclass(frozen=True)
class BaZiPilarHora:
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


@dataclass(frozen=True)
class DaimonHoraResult:
    planeta: str
    id_gatilho: int
    numero_hora: int
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


@dataclass(frozen=True)
class HDActivation:
    planeta: str
    longitude: float
    gate: int    # 1–64
    linha: int   # 1–6


@dataclass
class HDResult:
    personalidade: list[HDActivation]
    design: list[HDActivation]
    centros_definidos: frozenset[str]
    canais_ativos: list[tuple[int, int]]
    tipo: str
    estrategia: str
    tipo_id_gatilho: int
    autoridade: str
    autoridade_id_gatilho: int
    porta_sol_personalidade: int   # Porta do Sol de Personalidade (1–64)
    vote: int
    overall_status: TemporalStatus
    tipo_b: str | None = None
    estrategia_b: str | None = None
    tipo_b_id_gatilho: int | None = None
    porta_sol_personalidade_b: int | None = None
