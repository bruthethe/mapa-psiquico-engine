"""
Testes do motor Gematria (Hebraica e Grega).

Unitários: tokenize — dígrafos, qu→k, c/ce/ci, ç, acentos, rr/ss.
Integração: 5 nomes com resultados verificados manualmente.

Tabela Hebraica (valores relevantes para os testes):
  a=1  b=2  ch=300  d=4  e=5  f=80  g=3  h=5  i=10  j=7  k=20  l=30
  lh=30  m=40  n=50  nh=50  o=6  p=80  r=200  rr=200  s=60  ss=60
  t=400  u=6  v=6  w=6  x=60  y=10  z=7  c=20  ce=60  ci=60  ç=60

Tabela Grega (valores relevantes):
  a=1  b=2  ch=600  d=4  e=5  f=500  g=3  h=8  i=10  j=7  k=20  l=30
  lh=30  m=40  n=50  nh=50  o=70  p=80  r=100  rr=100  s=200  ss=200
  t=300  u=400  v=2  w=400  x=60  y=400  z=7  c=20  ce=200  ci=200  ç=200

Voto: ID do alfabeto com maior soma bruta (pré-redução); empate → Grego.
Exemplo do JSON: BRUNO → Hebr=264→3, Grego=622→1, Grego vence → vote=1.
"""

import pytest

from app.core.temporal import TemporalStatus
from app.motors.gematria import (
    GematriaResult,
    calculate_gematria,
    tokenize,
)

_VALID_IDS = frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33})


# ── Testes unitários — tokenize ───────────────────────────────────────────────


class TestTokenize:
    def test_simples(self):
        assert tokenize("ANA") == ["a", "n", "a"]

    def test_maiusculas_normalizadas(self):
        assert tokenize("BRUNO") == ["b", "r", "u", "n", "o"]

    def test_digrafos_lh_nh_ch(self):
        # lh, nh, ch são consumidos como token único
        assert tokenize("COELHO") == ["c", "o", "e", "lh", "o"]
        assert tokenize("NHOQUE") == ["nh", "o", "k", "e"]   # nh + qu→k
        assert tokenize("CHICO") == ["ch", "i", "c", "o"]

    def test_rr_ss_valor_unico(self):
        # rr e ss → token único (consoante dupla = valor simples)
        assert tokenize("TERRA") == ["t", "e", "rr", "a"]
        assert tokenize("PASSARO") == ["p", "a", "ss", "a", "r", "o"]

    def test_qu_antes_ei_vira_k(self):
        # qu antes de e/i → k (u mudo)
        assert tokenize("QUEIJO") == ["k", "e", "i", "j", "o"]
        assert tokenize("QUINTO") == ["k", "i", "n", "t", "o"]

    def test_qu_antes_nao_ei_permanece(self):
        # qu antes de a/o → q e u separados
        assert tokenize("QUARENTA") == ["q", "u", "a", "r", "e", "n", "t", "a"]

    def test_c_antes_ei(self):
        # c antes de e/i → token "ce" ou "ci" (Samekh/Sigma, não Kaph/Kappa)
        assert tokenize("CELIA") == ["ce", "l", "i", "a"]
        assert tokenize("CIRO") == ["ci", "r", "o"]

    def test_c_antes_nao_ei(self):
        # c antes de a/o/u → Kaph/Kappa
        assert tokenize("CARLOS") == ["c", "a", "r", "l", "o", "s"]

    def test_cedilha_token_proprio(self):
        # ç → token "ç" (Samekh=60/Sigma=200), não 'c' (Kaph=20)
        assert tokenize("GRAÇA") == ["g", "r", "a", "ç", "a"]

    def test_acento_strip(self):
        # acentos removidos pela NFD
        assert tokenize("JOSÉ") == ["j", "o", "s", "e"]
        assert tokenize("JOÃO") == ["j", "o", "a", "o"]   # ã → a

    def test_espaco_ignorado(self):
        # espaços não são alpha, são descartados
        assert tokenize("ANA PAULA") == ["a", "n", "a", "p", "a", "u", "l", "a"]

    def test_hifen_ignorado(self):
        assert tokenize("A-B") == ["a", "b"]


# ── Testes de integração — 5 nomes conhecidos ────────────────────────────────


@pytest.mark.integration
class TestCalculateGematria:
    """
    Resultados calculados manualmente token a token.
    Exemplo canônico BRUNO verificado contra data-gematria.json.
    """

    def test_bruno_exemplo_canonico(self):
        # Tokens: b, r, u, n, o
        # Hebr: b=2 + r=200 + u=6 + n=50 + o=6 = 264 → 2+6+4=12 → 3
        # Grego: b=2 + r=100 + u=400 + n=50 + o=70 = 622 → 6+2+2=10 → 1
        # Grego vence (622 > 264) → vote=lookup_id(1)=1
        r = calculate_gematria("BRUNO")
        assert r.id_hebraico == 3
        assert r.id_grego == 1
        assert r.vote == 1

    def test_ana_empate(self):
        # Tokens: a, n, a
        # Hebr: a=1 + n=50 + a=1 = 52 → 5+2=7
        # Grego: a=1 + n=50 + a=1 = 52 → 7
        # Empate → Grego desempata → vote=lookup_id(7)=7
        r = calculate_gematria("ANA")
        assert r.id_hebraico == 7
        assert r.id_grego == 7
        assert r.vote == 7

    def test_rafael_hebraico_mestre_11(self):
        # Tokens: r, a, f, a, e, l
        # Hebr: r=200 + a=1 + f=80 + a=1 + e=5 + l=30 = 317 → 3+1+7=11 (MESTRE!)
        # Grego: r=100 + a=1 + f=500 + a=1 + e=5 + l=30 = 637 → 6+3+7=16 → 7
        # Grego vence (637 > 317) → vote=lookup_id(7)=7
        r = calculate_gematria("RAFAEL")
        assert r.id_hebraico == 11
        assert r.id_grego == 7
        assert r.vote == 7

    def test_thiago_hebraico_vence_com_mestre_11(self):
        # Tokens: t, h, i, a, g, o  ("th" NÃO é dígrafo)
        # Hebr: t=400 + h=5 + i=10 + a=1 + g=3 + o=6 = 425 → 4+2+5=11 (MESTRE!)
        # Grego: t=300 + h=8 + i=10 + a=1 + g=3 + o=70 = 392 → 3+9+2=14 → 5
        # Hebraico vence (425 > 392) → vote=lookup_id(11)=11
        r = calculate_gematria("THIAGO")
        assert r.id_hebraico == 11
        assert r.id_grego == 5
        assert r.vote == 11

    def test_chico_digrafos_ch(self):
        # Tokens: ch, i, c, o  (ch=dígrafo; c antes de 'o' → Kaph/Kappa)
        # Hebr: ch=300 + i=10 + c=20 + o=6 = 336 → 3+3+6=12 → 3
        # Grego: ch=600 + i=10 + c=20 + o=70 = 700 → 7+0+0=7
        # Grego vence (700 > 336) → vote=lookup_id(7)=7
        r = calculate_gematria("CHICO")
        assert r.id_hebraico == 3
        assert r.id_grego == 7
        assert r.vote == 7

    def test_status_sempre_exact(self):
        r = calculate_gematria("BRUNO")
        assert r.overall_status == TemporalStatus.EXACT

    def test_vote_em_valid_ids(self):
        nomes = ["BRUNO", "ANA", "RAFAEL", "THIAGO", "CHICO",
                 "MARIA", "JOAO", "CARLOS", "LUCAS", "PAULO"]
        for nome in nomes:
            r = calculate_gematria(nome)
            assert r.vote in _VALID_IDS, f"vote inválido: {nome} → {r.vote}"
