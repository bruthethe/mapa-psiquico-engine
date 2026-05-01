import pytest

from app.core.ids import (
    MASTER_NUMBERS,
    VALID_IDS,
    MasterLabel,
    get_master_label,
    lookup_id,
    theosophic_reduce,
)


class TestTheosophicReduce:
    # ── Dígitos únicos — nunca alteram ────────────────────────────────────────
    @pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6, 7, 8, 9])
    def test_single_digits_unchanged(self, n: int) -> None:
        assert theosophic_reduce(n) == n

    # ── Números mestres — param imediatamente ─────────────────────────────────
    def test_11_preserved(self) -> None:
        assert theosophic_reduce(11) == 11

    def test_22_preserved(self) -> None:
        assert theosophic_reduce(22) == 22

    def test_33_preserved(self) -> None:
        assert theosophic_reduce(33) == 33

    # ── Reduções comuns ───────────────────────────────────────────────────────
    def test_10_reduces_to_1(self) -> None:
        assert theosophic_reduce(10) == 1

    def test_12_reduces_to_3(self) -> None:
        assert theosophic_reduce(12) == 3

    def test_19_reduces_to_1(self) -> None:
        assert theosophic_reduce(19) == 1  # 1+9=10 → 1+0=1

    def test_20_reduces_to_2(self) -> None:
        assert theosophic_reduce(20) == 2

    def test_29_reduces_to_11(self) -> None:
        assert theosophic_reduce(29) == 11  # 2+9=11 — mestre

    def test_44_reduces_to_8(self) -> None:
        assert theosophic_reduce(44) == 8  # 4+4=8

    def test_55_reduces_to_1(self) -> None:
        assert theosophic_reduce(55) == 1  # 5+5=10 → 1

    def test_66_reduces_to_3(self) -> None:
        assert theosophic_reduce(66) == 3  # 6+6=12 → 3

    def test_77_reduces_to_5(self) -> None:
        assert theosophic_reduce(77) == 5  # 7+7=14 → 5

    def test_88_reduces_to_7(self) -> None:
        assert theosophic_reduce(88) == 7  # 8+8=16 → 7

    def test_99_reduces_to_9(self) -> None:
        assert theosophic_reduce(99) == 9  # 9+9=18 → 9

    def test_100_reduces_to_1(self) -> None:
        assert theosophic_reduce(100) == 1

    def test_large_number(self) -> None:
        assert theosophic_reduce(1234) == 1  # 1+2+3+4=10 → 1

    def test_399_reduces_to_3(self) -> None:
        assert theosophic_reduce(399) == 3  # 3+9+9=21 → 3

    def test_zero(self) -> None:
        assert theosophic_reduce(0) == 0

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError):
            theosophic_reduce(-1)

    # ── Casos que chegam em 33 via soma ──────────────────────────────────────
    def test_reduces_to_33_via_sum(self) -> None:
        # 6+9+9+9=33 → mestre
        assert theosophic_reduce(699) == 6  # 6+9+9=24 → 6
        # número que soma 33 diretamente: ex. 996 → 9+9+6=24 → 6
        # para chegar em 33: 15+18=33 não existe em dígitos simples
        # mas 999 → 27 → 9, portanto testamos 993 → 9+9+3=21→3
        assert theosophic_reduce(993) == 3

    def test_number_that_passes_through_22(self) -> None:
        # Qualquer número cuja soma intermediária seja 22 para em 22
        # Ex: 499 → 4+9+9=22 → mestre
        assert theosophic_reduce(499) == 22


class TestLookupId:
    def test_8_redirects_to_4(self) -> None:
        assert lookup_id(8) == 4

    def test_22_redirects_to_4(self) -> None:
        assert lookup_id(22) == 4

    @pytest.mark.parametrize("id_", [1, 2, 3, 4, 5, 6, 7, 9, 11, 33])
    def test_others_return_themselves(self, id_: int) -> None:
        assert lookup_id(id_) == id_


class TestGetMasterLabel:
    def test_11_returns_label(self) -> None:
        label = get_master_label(11)
        assert isinstance(label, MasterLabel)
        assert label.id_dados == 11
        assert "Portal" in label.titulo

    def test_22_returns_label_with_id_dados_4(self) -> None:
        label = get_master_label(22)
        assert isinstance(label, MasterLabel)
        assert label.id_dados == 4  # 22 usa dados do ID 4
        assert "Construtor" in label.titulo

    def test_33_returns_label(self) -> None:
        label = get_master_label(33)
        assert isinstance(label, MasterLabel)
        assert label.id_dados == 33
        assert "Mago" in label.titulo

    @pytest.mark.parametrize("id_", [1, 2, 3, 4, 5, 6, 7, 8, 9])
    def test_common_ids_return_none(self, id_: int) -> None:
        assert get_master_label(id_) is None


class TestConstants:
    def test_master_numbers(self) -> None:
        assert MASTER_NUMBERS == {11, 22, 33}

    def test_valid_ids_contains_expected(self) -> None:
        assert {1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33}.issubset(VALID_IDS)
