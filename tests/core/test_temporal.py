from datetime import datetime, time

import pytest

from app.core.temporal import (
    local_to_utc,
    TemporalStatus,
    TimeInput,
    TimeInputType,
    TimeWindow,
    parse_time_input,
    resolve_status,
)


class TestParseExact:
    def test_type_is_exact(self) -> None:
        result = parse_time_input(exact_time=time(14, 35))
        assert result.type == TimeInputType.EXACT

    def test_both_points_equal_to_input(self) -> None:
        t = time(14, 35)
        result = parse_time_input(exact_time=t)
        assert result.point_a == t
        assert result.point_b == t

    def test_midnight_is_valid(self) -> None:
        result = parse_time_input(exact_time=time(0, 0))
        assert result.point_a == time(0, 0)

    def test_end_of_day_is_valid(self) -> None:
        result = parse_time_input(exact_time=time(23, 59))
        assert result.point_a == time(23, 59)


class TestParseWindow:
    @pytest.mark.parametrize("window, expected_a, expected_b", [
        (TimeWindow.MADRUGADA,   time(0, 0),  time(3, 59)),
        (TimeWindow.MANHA_CEDO,  time(4, 0),  time(7, 59)),
        (TimeWindow.MANHA,       time(8, 0),  time(11, 59)),
        (TimeWindow.TARDE,       time(12, 0), time(15, 59)),
        (TimeWindow.FINAL_TARDE, time(16, 0), time(19, 59)),
        (TimeWindow.NOITE,       time(20, 0), time(23, 59)),
    ])
    def test_window_bounds(self, window: TimeWindow, expected_a: time, expected_b: time) -> None:
        result = parse_time_input(window=window)
        assert result.type == TimeInputType.WINDOW
        assert result.point_a == expected_a
        assert result.point_b == expected_b


class TestParseUnknown:
    def test_type_is_unknown(self) -> None:
        result = parse_time_input()
        assert result.type == TimeInputType.UNKNOWN

    def test_fallback_is_noon(self) -> None:
        result = parse_time_input()
        assert result.point_a == time(12, 0)
        assert result.point_b == time(12, 0)

    def test_both_points_equal(self) -> None:
        result = parse_time_input()
        assert result.point_a == result.point_b


class TestResolveStatus:
    def test_exact_always_returns_status_3(self) -> None:
        ti = parse_time_input(exact_time=time(10, 0))
        assert resolve_status(ti, 1, 1) == TemporalStatus.EXACT

    def test_window_same_ids_returns_status_2(self) -> None:
        ti = parse_time_input(window=TimeWindow.TARDE)
        assert resolve_status(ti, 5, 5) == TemporalStatus.SAFE

    def test_window_different_ids_returns_status_1(self) -> None:
        ti = parse_time_input(window=TimeWindow.MANHA)
        assert resolve_status(ti, 5, 7) == TemporalStatus.HYBRID

    def test_unknown_same_ids_returns_status_2(self) -> None:
        ti = parse_time_input()
        assert resolve_status(ti, 3, 3) == TemporalStatus.SAFE

    def test_unknown_different_ids_returns_status_1(self) -> None:
        # Motor sinaliza cúspide passando IDs distintos para o mesmo ponto de tempo
        ti = parse_time_input()
        assert resolve_status(ti, 3, 4) == TemporalStatus.HYBRID

    def test_status_values_are_correct_ints(self) -> None:
        assert TemporalStatus.HYBRID == 1
        assert TemporalStatus.SAFE == 2
        assert TemporalStatus.EXACT == 3


class TestLocalToUtc:
    def test_sao_paulo_utc_minus_3(self) -> None:
        local = datetime(1990, 5, 15, 14, 30)
        result = local_to_utc(local, "America/Sao_Paulo")
        assert result == datetime(1990, 5, 15, 17, 30)

    def test_utc_zone_no_offset(self) -> None:
        local = datetime(2000, 1, 1, 12, 0)
        result = local_to_utc(local, "UTC")
        assert result == datetime(2000, 1, 1, 12, 0)

    def test_result_is_naive(self) -> None:
        local = datetime(1990, 5, 15, 10, 0)
        result = local_to_utc(local, "America/Sao_Paulo")
        assert result.tzinfo is None

    def test_dst_transition_sao_paulo_summer(self) -> None:
        # During Brazilian DST (Nov–Feb), BRT is UTC-2 instead of UTC-3
        local = datetime(1990, 12, 15, 14, 30)
        result = local_to_utc(local, "America/Sao_Paulo")
        assert result == datetime(1990, 12, 15, 16, 30)

    def test_new_york_utc_minus_5(self) -> None:
        local = datetime(2024, 3, 1, 8, 0)
        result = local_to_utc(local, "America/New_York")
        assert result == datetime(2024, 3, 1, 13, 0)

    def test_tokyo_utc_plus_9(self) -> None:
        local = datetime(2024, 6, 15, 9, 0)
        result = local_to_utc(local, "Asia/Tokyo")
        assert result == datetime(2024, 6, 15, 0, 0)
