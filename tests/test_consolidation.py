"""
Testes da consolidação do dominant archetype ID.

A consolidação recebe os votos dos 10 motores (6 Fase 1 temporal + 4 Fase 2 nominal)
e elege o dominant archetype ID seguindo:
  1. Maior frequência
  2. Empate → preferência a IDs com voto na Fase 1
  3. Empate persistente → menor ID numérico

Status EXACT: sem dual-check (hora exata ou fallback sem cúspide)
Status SAFE:  dual-check convergiu (A = B)
Status HYBRID: dual-check divergiu (A ≠ B) → dois IDs simultâneos

Nota: os votos chegam já pós-lookup_id (ID 8 → 4, ID 22 → 4 pelos motores),
portanto id_dominante nunca será 22; master_label aplica-se a 11 e 33.
"""

import pytest

from app.core.consolidation import ConsolidationResult, consolidate, _elect
from app.core.temporal import TemporalStatus


# ── Testes unitários — _elect ─────────────────────────────────────────────────


class TestElect:

    def test_vencedor_claro_por_frequencia(self):
        # ID 1 tem 4 votos (3 Fase 1 + 1 Fase 2) — vence sem empate
        assert _elect([1, 1, 1, 3, 5, 6], [1, 2, 3, 4]) == 1

    def test_empate_fase1_bate_fase2(self):
        # 1, 2, 3, 4 todos com 2 votos; 1 e 3 estão na Fase 1 → menor entre {1,3} = 1
        assert _elect([1, 1, 3, 3, 5, 6], [2, 2, 4, 4]) == 1

    def test_empate_ambos_fase1_menor_vence(self):
        # 1 e 3 empatados a 3 votos cada, ambos na Fase 1 → menor = 1
        assert _elect([1, 1, 3, 3, 5, 6], [1, 3, 4, 4]) == 1

    def test_empate_nenhum_fase1_menor_vence(self):
        # Fase 1 fragmentada; 3 e 4 empatados a 2 votos só na Fase 2 → menor = 3
        assert _elect([1, 2, 5, 6, 7, 9], [3, 3, 4, 4]) == 3

    def test_todos_votos_iguais(self):
        assert _elect([5, 5, 5, 5, 5, 5], [5, 5, 5, 5]) == 5

    def test_vencedor_de_fase2_quando_mais_frequente(self):
        # Fase 2 pode vencer se não houver empate com Fase 1
        # ID 9 tem 3 votos de Fase 2 vs IDs de Fase 1 com 1 cada
        assert _elect([1, 2, 3, 4, 5, 6], [9, 9, 9, 7]) == 9

    def test_erro_sem_votos(self):
        with pytest.raises(ValueError):
            _elect([], [])


# ── Testes de integração — consolidate ───────────────────────────────────────


class TestConsolidate:

    # ── Status EXACT (sem dual-check) ────────────────────────────────────────

    def test_exact_vencedor_unico(self):
        r = consolidate([1, 1, 1, 3, 5, 6], [1, 2, 3, 4])
        assert r.id_dominante == 1
        assert r.id_dominante_b is None
        assert r.status == TemporalStatus.EXACT

    def test_exact_sem_fase1_b_retorna_exact(self):
        r = consolidate([3, 3, 3, 5, 6, 7], [3, 2, 4, 5], votes_fase1_b=None)
        assert r.status == TemporalStatus.EXACT

    # ── Cenários de empate ────────────────────────────────────────────────────

    def test_empate_fase1_decide(self):
        # 1,2,3,4 empatados; Fase 1 tem 1 e 3 → menor = 1
        r = consolidate([1, 1, 3, 3, 5, 6], [2, 2, 4, 4])
        assert r.id_dominante == 1

    def test_empate_dentro_fase1_menor_decide(self):
        # 1 e 3 empatados, ambos na Fase 1 → 1 vence
        r = consolidate([1, 1, 3, 3, 5, 6], [1, 3, 4, 4])
        assert r.id_dominante == 1

    def test_empate_so_fase2_menor_decide(self):
        # Fase 1 completamente fragmentada; 3 e 4 empatados só via Fase 2 → 3 vence
        r = consolidate([1, 2, 5, 6, 7, 9], [3, 3, 4, 4])
        assert r.id_dominante == 3

    # ── Status 1 — dual-check diverge ─────────────────────────────────────────

    def test_hybrid_ids_distintos(self):
        # Ponto A elege 1, ponto B elege 3 → HYBRID com dois IDs
        r = consolidate(
            votes_fase1=[1, 1, 1, 3, 5, 6],
            votes_fase2=[1, 2, 3, 4],
            votes_fase1_b=[3, 3, 3, 1, 5, 6],
        )
        assert r.id_dominante == 1
        assert r.id_dominante_b == 3
        assert r.status == TemporalStatus.HYBRID

    def test_hybrid_ids_iguais_vira_safe(self):
        # Ponto A e B convergem no mesmo ID → SAFE, um único ID
        r = consolidate(
            votes_fase1=[1, 1, 1, 3, 5, 6],
            votes_fase2=[1, 2, 3, 4],
            votes_fase1_b=[1, 1, 3, 3, 5, 6],  # 1 e 3 empatados → 1 vence (Fase 1 + menor)
        )
        assert r.id_dominante == 1
        assert r.id_dominante_b is None
        assert r.status == TemporalStatus.SAFE

    # ── Master labels ─────────────────────────────────────────────────────────

    def test_master_label_11(self):
        r = consolidate([11, 11, 11, 3, 5, 6], [11, 2, 3, 4])
        assert r.id_dominante == 11
        assert r.master_label is not None
        assert r.master_label.id_dados == 11

    def test_master_label_33(self):
        r = consolidate([33, 33, 33, 3, 5, 6], [33, 2, 3, 4])
        assert r.id_dominante == 33
        assert r.master_label is not None
        assert r.master_label.id_dados == 33

    def test_sem_master_label_para_id_comum(self):
        r = consolidate([1, 1, 1, 3, 5, 6], [1, 2, 3, 4])
        assert r.master_label is None

    def test_master_label_b_em_hybrid(self):
        # Ponto B elege 33 → master_label_b preenchido
        r = consolidate(
            votes_fase1=[1, 1, 1, 3, 5, 6],
            votes_fase2=[1, 2, 3, 4],
            votes_fase1_b=[33, 33, 33, 1, 5, 6],
        )
        assert r.id_dominante == 1
        assert r.id_dominante_b == 33
        assert r.master_label is None
        assert r.master_label_b is not None
        assert r.master_label_b.id_dados == 33

    def test_master_label_b_none_quando_safe(self):
        r = consolidate(
            votes_fase1=[1, 1, 1, 3, 5, 6],
            votes_fase2=[1, 2, 3, 4],
            votes_fase1_b=[1, 1, 3, 3, 5, 6],
        )
        assert r.master_label_b is None
