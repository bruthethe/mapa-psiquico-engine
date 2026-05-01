"""
Geocoding via OpenStreetMap Nominatim.

Converte cidade + estado + país em coordenadas geográficas e timezone.
Sem chave de API — respeitar o rate limit de 1 req/s do Nominatim.
"""

from dataclasses import dataclass
from functools import lru_cache

import httpx
from timezonefinder import TimezoneFinder

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_USER_AGENT = "MapaPsiquico/0.1 (brunothethe@gmail.com)"
_TF = TimezoneFinder()


class GeocodingError(Exception):
    """Lançado quando a cidade não é encontrada ou o timezone não pode ser resolvido."""


@dataclass(frozen=True)
class GeoLocation:
    city: str
    state: str
    country: str
    latitude: float
    longitude: float
    timezone: str  # ex: "America/Sao_Paulo"


@lru_cache(maxsize=512)
def geocode(city: str, state: str = "", country: str = "") -> GeoLocation:
    """
    Converte cidade + estado + país em coordenadas e timezone.

    Resultados são cacheados em memória — a mesma cidade não gera
    múltiplas requisições HTTP durante a vida do processo.

    Raises:
        GeocodingError: se a cidade não for encontrada ou o timezone não puder ser resolvido.
        httpx.HTTPError: se a API do Nominatim estiver indisponível.
    """
    query = ", ".join(filter(None, [city, state, country]))

    response = httpx.get(
        _NOMINATIM_URL,
        params={"q": query, "format": "json", "limit": 1},
        headers={"User-Agent": _USER_AGENT},
        timeout=10.0,
    )
    response.raise_for_status()

    results = response.json()
    if not results:
        raise GeocodingError(f"Cidade não encontrada: {query!r}")

    lat = float(results[0]["lat"])
    lon = float(results[0]["lon"])

    tz = _TF.timezone_at(lat=lat, lng=lon)
    if tz is None:
        raise GeocodingError(
            f"Timezone não encontrado para coordenadas: ({lat:.4f}, {lon:.4f})"
        )

    return GeoLocation(
        city=city,
        state=state,
        country=country,
        latitude=lat,
        longitude=lon,
        timezone=tz,
    )
