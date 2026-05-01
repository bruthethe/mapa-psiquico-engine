from unittest.mock import MagicMock, patch

import pytest

from app.core.geocoding import GeoLocation, GeocodingError, geocode

# Resposta simulada do Nominatim para São Paulo
_SP_RESPONSE = [{"lat": "-23.5505", "lon": "-46.6333", "display_name": "São Paulo, SP, Brasil"}]

# Resposta simulada para Londres (fuso diferente — valida timezone)
_LDN_RESPONSE = [{"lat": "51.5074", "lon": "-0.1278", "display_name": "London, England"}]


def _mock_get(response_data: list) -> MagicMock:
    mock = MagicMock()
    mock.json.return_value = response_data
    mock.raise_for_status.return_value = None
    return mock


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    geocode.cache_clear()
    yield
    geocode.cache_clear()


class TestGeocode:
    @patch("app.core.geocoding.httpx.get")
    def test_returns_geolocation(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_SP_RESPONSE)
        result = geocode("São Paulo", "SP", "Brasil")
        assert isinstance(result, GeoLocation)

    @patch("app.core.geocoding.httpx.get")
    def test_coordinates_parsed_correctly(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_SP_RESPONSE)
        result = geocode("São Paulo", "SP", "Brasil")
        assert result.latitude == pytest.approx(-23.5505)
        assert result.longitude == pytest.approx(-46.6333)

    @patch("app.core.geocoding.httpx.get")
    def test_timezone_resolved_for_sao_paulo(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_SP_RESPONSE)
        result = geocode("São Paulo", "SP", "Brasil")
        assert result.timezone == "America/Sao_Paulo"

    @patch("app.core.geocoding.httpx.get")
    def test_timezone_resolved_for_london(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_LDN_RESPONSE)
        result = geocode("London", "", "England")
        assert result.timezone == "Europe/London"

    @patch("app.core.geocoding.httpx.get")
    def test_input_fields_preserved(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_SP_RESPONSE)
        result = geocode("São Paulo", "SP", "Brasil")
        assert result.city == "São Paulo"
        assert result.state == "SP"
        assert result.country == "Brasil"

    @patch("app.core.geocoding.httpx.get")
    def test_timezone_is_valid_format(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_SP_RESPONSE)
        result = geocode("São Paulo", "SP", "Brasil")
        assert "/" in result.timezone  # ex: "America/Sao_Paulo"

    @patch("app.core.geocoding.httpx.get")
    def test_geolocation_is_immutable(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_SP_RESPONSE)
        result = geocode("São Paulo", "SP", "Brasil")
        with pytest.raises((AttributeError, TypeError)):
            result.latitude = 0.0  # type: ignore[misc]

    @patch("app.core.geocoding.httpx.get")
    def test_city_not_found_raises_geocoding_error(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get([])
        with pytest.raises(GeocodingError, match="não encontrada"):
            geocode("CidadeQueNaoExiste", "", "")

    @patch("app.core.geocoding.httpx.get")
    def test_cache_prevents_duplicate_http_requests(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_SP_RESPONSE)
        geocode("São Paulo", "SP", "Brasil")
        geocode("São Paulo", "SP", "Brasil")
        assert mock_get.call_count == 1

    @patch("app.core.geocoding.httpx.get")
    def test_different_cities_make_separate_requests(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_SP_RESPONSE)
        geocode("São Paulo", "SP", "Brasil")
        mock_get.return_value = _mock_get(_LDN_RESPONSE)
        geocode("London", "", "England")
        assert mock_get.call_count == 2

    @patch("app.core.geocoding.httpx.get")
    def test_nominatim_query_includes_all_fields(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_SP_RESPONSE)
        geocode("São Paulo", "SP", "Brasil")
        call_params = mock_get.call_args.kwargs["params"]
        assert "São Paulo" in call_params["q"]
        assert "SP" in call_params["q"]
        assert "Brasil" in call_params["q"]

    @patch("app.core.geocoding.httpx.get")
    def test_optional_state_and_country(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_SP_RESPONSE)
        result = geocode("São Paulo")
        assert isinstance(result, GeoLocation)
        assert result.state == ""
        assert result.country == ""
