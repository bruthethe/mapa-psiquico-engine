from unittest.mock import MagicMock, patch

import pytest

from app.core.geocoding import GeocodingError, GeoLocation, geocode

# Resposta simulada do Nominatim para Londres (cidade de referência neutra)
_LDN_RESPONSE = [
    {"lat": "51.5074", "lon": "-0.1278", "display_name": "London, England"}
]

# Resposta simulada para Tóquio (fuso diferente — valida timezone)
_TKY_RESPONSE = [
    {"lat": "35.6762", "lon": "139.6503", "display_name": "Tokyo, Japan"}
]


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
        mock_get.return_value = _mock_get(_LDN_RESPONSE)
        result = geocode("London", "", "England")
        assert isinstance(result, GeoLocation)

    @patch("app.core.geocoding.httpx.get")
    def test_coordinates_parsed_correctly(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_LDN_RESPONSE)
        result = geocode("London", "", "England")
        assert result.latitude == pytest.approx(51.5074)
        assert result.longitude == pytest.approx(-0.1278)

    @patch("app.core.geocoding.httpx.get")
    def test_timezone_resolved_for_london(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_LDN_RESPONSE)
        result = geocode("London", "", "England")
        assert result.timezone == "Europe/London"

    @patch("app.core.geocoding.httpx.get")
    def test_timezone_resolved_for_tokyo(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_TKY_RESPONSE)
        result = geocode("Tokyo", "", "Japan")
        assert result.timezone == "Asia/Tokyo"

    @patch("app.core.geocoding.httpx.get")
    def test_input_fields_preserved(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_LDN_RESPONSE)
        result = geocode("London", "England", "UK")
        assert result.city == "London"
        assert result.state == "England"
        assert result.country == "UK"

    @patch("app.core.geocoding.httpx.get")
    def test_timezone_is_valid_format(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_LDN_RESPONSE)
        result = geocode("London", "", "England")
        assert "/" in result.timezone

    @patch("app.core.geocoding.httpx.get")
    def test_geolocation_is_immutable(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_LDN_RESPONSE)
        result = geocode("London", "", "England")
        with pytest.raises((AttributeError, TypeError)):
            result.latitude = 0.0  # type: ignore[misc]

    @patch("app.core.geocoding.httpx.get")
    def test_city_not_found_raises_geocoding_error(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get([])
        with pytest.raises(GeocodingError, match="não encontrada"):
            geocode("CidadeQueNaoExiste", "", "")

    @patch("app.core.geocoding.httpx.get")
    def test_cache_prevents_duplicate_http_requests(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_LDN_RESPONSE)
        geocode("London", "", "England")
        geocode("London", "", "England")
        assert mock_get.call_count == 1

    @patch("app.core.geocoding.httpx.get")
    def test_different_cities_make_separate_requests(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_LDN_RESPONSE)
        geocode("London", "", "England")
        mock_get.return_value = _mock_get(_TKY_RESPONSE)
        geocode("Tokyo", "", "Japan")
        assert mock_get.call_count == 2

    @patch("app.core.geocoding.httpx.get")
    def test_nominatim_query_includes_all_fields(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_LDN_RESPONSE)
        geocode("London", "England", "UK")
        call_params = mock_get.call_args.kwargs["params"]
        assert "London" in call_params["q"]
        assert "England" in call_params["q"]
        assert "UK" in call_params["q"]

    @patch("app.core.geocoding.httpx.get")
    def test_optional_state_and_country(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_get(_LDN_RESPONSE)
        result = geocode("London")
        assert isinstance(result, GeoLocation)
        assert result.state == ""
        assert result.country == ""
