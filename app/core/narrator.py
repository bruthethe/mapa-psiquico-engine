"""Narrator — gera texto narrativo interpretativo via Claude Haiku."""

from __future__ import annotations

import json
import logging
import os

import anthropic

logger = logging.getLogger(__name__)

_MODEL = "claude-haiku-4-5-20251001"

_SYSTEM_PROMPT = """\
Você é o narrador de um relatório arquetípico — profundo, poético e acessível.
Transforma dados simbólicos em linguagem humanizada para o leitor.

Diretrizes inegociáveis:
- Português do Brasil; tom contemplativo, direto, empático
- Parágrafos corridos de 2 a 4 frases; nunca liste campos ou nomeie sistemas técnicos
- Zero jargão técnico ou esotérico: traduza tudo em experiência humana vivível
- Voz direta ao leitor (você), no presente, afirmativa
- Sem clichês new-age ("energia", "vibração elevada", "caminho da alma")

Gênero do leitor:
- O campo "genero" indica: "masculino", "feminino" ou "neutro"
- Use esse gênero em todos os adjetivos, pronomes e concordâncias
- Se "neutro": evite marcação de gênero

Formato de saída:
- JSON puro, sem markdown, sem texto fora das chaves
- "dados" copiados do input são reproduzidos literalmente — não invente nem altere valores
- "texto" contém apenas os parágrafos solicitados, cada um como string corrida\
"""

_INSTRUCAO_LOTE_1 = """\
Gere a narrativa para os capítulos 1 a 6. Retorne JSON puro conforme o formato abaixo.
Cada texto: 2 a 4 frases corridas; nunca liste campos nem nomeie sistemas.

cap1 — 4 cards de arquétipos:
  retorne os 4 objetos: essencia_solar, mascara, refugio_lunar, sombra
  cada objeto: { nome, tipo, texto }
  - essencia_solar.nome ← arquetipos.essencia_solar; tipo = "essencia_solar"
  - mascara.nome ← arquetipos.mascara; tipo = "mascara"
  - refugio_lunar.nome ← arquetipos.refugio_lunar; tipo = "refugio_lunar"
  - sombra.nome ← goetia.demonio; tipo = "sombra"
  NÃO inclua o campo "necessidade"
  texto de cada card: como este arquétipo específico se manifesta na vida do leitor

cap2 — Luminares e Temperamentos:
  luminares: array de 3 objetos { planeta, signo (copiados), texto (gerado) }
    - texto por luminar: como este planeta neste signo se expressa no cotidiano do leitor
  planetas: { lista (copiada de "planetas" do input), texto: o padrão sistêmico que emerge }
  temperamentos: { elemento_dominante, elemento_secundario, temperamento_dominante,
    temperamento_secundario (copiados), texto: padrão de comportamento e relação com a realidade }

cap3 — Védica:
  nakshatra_nome: copiado de nakshatra.nome
  atmakaraka: graha traduzido para PT (surya→Sol, chandra→Lua, mangala→Marte,
    budha→Mercúrio, guru→Júpiter, shukra→Vênus, shani→Saturno)
  purushartha: copiado
  texto_nakshatra: nakshatra, deidade e símbolo como retrato do propósito kármico desta vida
  texto_destino: atmakaraka + purushartha como vocação de fundo — o que a alma veio aprender

cap4 — Ba Zi:
  pilares: array de 4 objetos { pilar, animal, elemento (copiados), texto (gerado) }
    - pilar_ano → pilar = "ano", pilar_mes → "mes", pilar_dia → "dia", pilar_hora → "hora"
    - texto por pilar: influência específica deste pilar no caráter e destino do leitor
  texto_integracao: tensões e complementaridades entre os 4 pilares como padrão interno

cap5 — Tzolkin:
  kin: { kin (copiado), selo_nome (copiado de selo.nome), selo_cor (copiado de selo.cor),
         tom (format: "<tom.tom> · <tom.nome>"), texto: identidade sagrada no ciclo de tempo }
  oraculo: array de 4 objetos, na ordem: guia, analogo, antipoda, oculto
    cada objeto: { posicao, selo_nome (de <posicao>.nome), selo_cor (de <posicao>.cor),
                   essencia (de <posicao>.essencia) (todos copiados), texto (gerado) }
    texto por posição: o que este selo nesta posição oferece, desafia ou sustenta

cap6 — Numerologia:
  caminho_vida: copiado de pitagorica.caminho_vida
  numero_destino: copiado de caldeia.numero_destino
  sistemas: { pitagorica: { caminho_vida, alma, persona, expressao },
              cabalistica: { missao, motivacao, impressao, expressao },
              caldeia: { numero_destino, vibracao_psiquica },
              gematria: { resultado } } — copiados dos respectivos subcampos
  texto: os sistemas como convergência — o fio que une; use os números como âncoras, sem nomear escolas

Formato de resposta (JSON puro):
{
  "capitulos": {
    "cap1": {
      "essencia_solar": {"nome": "...", "tipo": "essencia_solar", "texto": "..."},
      "mascara":        {"nome": "...", "tipo": "mascara",        "texto": "..."},
      "refugio_lunar":  {"nome": "...", "tipo": "refugio_lunar",  "texto": "..."},
      "sombra":         {"nome": "...", "tipo": "sombra",         "texto": "..."}
    },
    "cap2": {
      "luminares": [
        {"planeta": "sol",        "signo": "...", "texto": "..."},
        {"planeta": "lua",        "signo": "...", "texto": "..."},
        {"planeta": "ascendente", "signo": "...", "texto": "..."}
      ],
      "planetas": {"lista": [...], "texto": "..."},
      "temperamentos": {"elemento_dominante": "...", "elemento_secundario": "...",
                        "temperamento_dominante": "...", "temperamento_secundario": "...",
                        "texto": "..."}
    },
    "cap3": {
      "nakshatra_nome": "...", "atmakaraka": "...", "purushartha": "...",
      "texto_nakshatra": "...", "texto_destino": "..."
    },
    "cap4": {
      "pilares": [
        {"pilar": "ano",  "animal": "...", "elemento": "...", "texto": "..."},
        {"pilar": "mes",  "animal": "...", "elemento": "...", "texto": "..."},
        {"pilar": "dia",  "animal": "...", "elemento": "...", "texto": "..."},
        {"pilar": "hora", "animal": "...", "elemento": "...", "texto": "..."}
      ],
      "texto_integracao": "..."
    },
    "cap5": {
      "kin": {"kin": 0, "selo_nome": "...", "selo_cor": "...", "tom": "...", "texto": "..."},
      "oraculo": [
        {"posicao": "guia",     "selo_nome": "...", "selo_cor": "...", "essencia": "...", "texto": "..."},
        {"posicao": "analogo",  "selo_nome": "...", "selo_cor": "...", "essencia": "...", "texto": "..."},
        {"posicao": "antipoda", "selo_nome": "...", "selo_cor": "...", "essencia": "...", "texto": "..."},
        {"posicao": "oculto",   "selo_nome": "...", "selo_cor": "...", "essencia": "...", "texto": "..."}
      ]
    },
    "cap6": {"caminho_vida": 0, "numero_destino": 0, "sistemas": {...}, "texto": "..."}
  }
}\
"""

_INSTRUCAO_LOTE_2 = """\
Gere a narrativa para os capítulos 7 a 12. Retorne JSON puro conforme o formato abaixo.
Cada texto: 2 a 4 frases corridas; nunca liste campos nem nomeie sistemas.

cap7 — Tarô e I Ching:
  taro:   { arcano (copiado), nome_arcano (copiado), texto: o arcano como espelho da fase atual }
  iching: { hexagrama (copiado), nome (copiado), texto: o hexagrama como conselho para agora }

cap8_9 (Alquimia + Daimon — dois sistemas, um texto unificado):
  signo_solar, elemento, fase, operacao (copiados de cap8)
  daimon_planeta (copiado de cap9.planeta)
  daimon_numero (copiado de cap9.numero_hora)
  texto: fase alquímica e guardião da hora como forças complementares — onde o leitor está
    no processo de transformação e quem o acompanhou na chegada ao mundo

cap10 — Panteões:
  divindades: array de 14 objetos, iterando sobre panteoes.divindades
  cada objeto: { nome (valor do dict), pantheon (chave do dict), texto (gerado) }
  Use contexto.id_dominante para relacionar cada divindade ao arquétipo dominante
  texto por divindade: 3 frases relacionando esse ser mítico ao perfil arquetípico do leitor

cap11 — Materialização Sensorial:
  cor, metal, cristal, erva, nota, geometria, animais, criatura (copiados de materializacao)
  texto: esses elementos como extensão simbólica do arquétipo — como expressam quem o leitor é
    no mundo material e sensorial

Formato de resposta (JSON puro):
{
  "capitulos": {
    "cap7": {
      "taro":   {"arcano": 0, "nome_arcano": "...", "texto": "..."},
      "iching": {"hexagrama": 0, "nome": "...", "texto": "..."}
    },
    "cap8_9": {
      "signo_solar": "...", "elemento": "...", "fase": "...", "operacao": "...",
      "daimon_planeta": "...", "daimon_numero": 0, "texto": "..."
    },
    "cap10": {
      "divindades": [
        {"nome": "...", "pantheon": "arcanjo",          "texto": "..."},
        {"nome": "...", "pantheon": "dogon",             "texto": "..."},
        {"nome": "...", "pantheon": "egipcio",           "texto": "..."},
        {"nome": "...", "pantheon": "grego",             "texto": "..."},
        {"nome": "...", "pantheon": "inca",              "texto": "..."},
        {"nome": "...", "pantheon": "inuit",             "texto": "..."},
        {"nome": "...", "pantheon": "ioruba",            "texto": "..."},
        {"nome": "...", "pantheon": "maia",              "texto": "..."},
        {"nome": "...", "pantheon": "maori",             "texto": "..."},
        {"nome": "...", "pantheon": "nordico",           "texto": "..."},
        {"nome": "...", "pantheon": "norte-americano",   "texto": "..."},
        {"nome": "...", "pantheon": "tao",               "texto": "..."},
        {"nome": "...", "pantheon": "tupi-guarani",      "texto": "..."},
        {"nome": "...", "pantheon": "xinto",             "texto": "..."}
      ]
    },
    "cap11": {
      "cor": "...", "metal": "...", "cristal": "...", "erva": "...",
      "nota": "...", "geometria": "...", "animais": {...}, "criatura": "...",
      "texto": "..."
    }
  }
}\
"""

_INSTRUCAO_LOTE_3 = """\
Você recebe um digest compacto com os fios condutores do relatório completo de 12 capítulos.
Gere o prefácio e a conclusão.

prefacio: 1 parágrafo (4 a 6 frases) que acolhe o leitor pelo arquétipo dominante e anuncia
  o que o relatório revela — use arquétipo, signo solar, caminho de vida e nakshatra como âncoras;
  não descreva o que cada capítulo vai mostrar, apenas abra o espaço

conclusao: 1 a 2 parágrafos que sintetizam TENSÕES fecundas — não repita o que foi dito nos
  capítulos; aponte contradições produtivas entre os dados (ex: temperamento Terra dominante
  mas propósito solar em Fogo; Caminho de Vida 5 mas Lua em Capricórnio); mostre o que o leitor
  terá que integrar, sem dar respostas definitivas; termine com abertura, não com fechamento

Formato de resposta (JSON puro):
{
  "prefacio": "...",
  "conclusao": "..."
}\
"""

_STRIP_KEYS: frozenset[str] = frozenset({
    "id_gatilho", "id_gatilho_b",
    "tipo_id_gatilho", "tipo_b_id_gatilho",
    "autoridade_id_gatilho",
    "vote", "vote_b", "voto",
    "status", "overall_status", "status_temporal",
    "fallback", "ajuste_frequencia", "sistema",
    "index",
    "id_dados",
    "longitude",
    "personalidade",
    "design",
})

_GRAHA_PT: dict[str, str] = {
    "surya":   "Sol",
    "chandra": "Lua",
    "mangala": "Marte",
    "budha":   "Mercúrio",
    "guru":    "Júpiter",
    "shukra":  "Vênus",
    "shani":   "Saturno",
    "rahu":    "Rahu (Nó Norte)",
    "ketu":    "Ketu (Nó Sul)",
}

_PERIODO_PT: dict[str, str] = {
    "diurno":  "nascido durante o dia",
    "noturno": "nascido durante a noite",
}

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY não configurada.")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def _translate_scalar(key: str, value: object) -> object:
    if not isinstance(value, str):
        return value
    if key == "graha":
        return _GRAHA_PT.get(value, value)
    if key in ("periodo", "periodo_b"):
        return _PERIODO_PT.get(value, value)
    return value


def _clean(data: object, parent_key: str = "") -> object:
    """Remove campos internos e traduz valores técnicos recursivamente."""
    if isinstance(data, dict):
        out: dict[str, object] = {}
        for k, v in data.items():
            if k in _STRIP_KEYS:
                continue
            if v is None and k.endswith("_b"):
                continue
            out[k] = _clean(v, parent_key=k)
        return out
    if isinstance(data, list):
        return [_clean(item, parent_key=parent_key) for item in data]
    return _translate_scalar(parent_key, data)


def _build_digest(caps: dict, prefacio: dict, genero: str) -> dict:
    """Extrai fios condutores compactos de todos os capítulos para o 3º lote."""
    digest: dict = {"genero": genero, "id_dominante": prefacio.get("id_dominante")}

    if cap1 := caps.get("cap1"):
        arq = cap1.get("arquetipos") or {}
        goe = cap1.get("goetia") or {}
        digest["arquetipo"] = {
            "essencia_solar": arq.get("essencia_solar"),
            "mascara": arq.get("mascara"),
            "sombra": goe.get("demonio"),
        }

    if cap2 := caps.get("cap2"):
        sol = cap2.get("sol") or {}
        lua = cap2.get("lua") or {}
        asc = cap2.get("ascendente") or {}
        temp = cap2.get("temperamentos") or {}
        digest["astro"] = {
            "sol": sol.get("sign"),
            "lua": lua.get("sign"),
            "ascendente": asc.get("sign"),
            "elemento_dominante": temp.get("elemento_dominante"),
            "temperamento_dominante": temp.get("temperamento_dominante"),
        }

    if cap3 := caps.get("cap3"):
        nak = cap3.get("nakshatra") or {}
        digest["vedica"] = {
            "nakshatra": nak.get("nome"),
            "purushartha": cap3.get("purushartha"),
        }

    if cap4 := caps.get("cap4"):
        dia = cap4.get("pilar_dia") or {}
        digest["bazi_dia"] = {
            "animal": dia.get("animal"),
            "elemento": dia.get("elemento"),
        }

    if cap6 := caps.get("cap6"):
        pit = cap6.get("pitagorica") or {}
        cal = cap6.get("caldeia") or {}
        digest["numerologia"] = {
            "caminho_vida": pit.get("caminho_vida"),
            "numero_destino": cal.get("numero_destino"),
        }

    if cap8 := caps.get("cap8"):
        digest["alquimia"] = {"fase": cap8.get("fase")}

    if cap9 := caps.get("cap9"):
        digest["daimon"] = {"planeta": cap9.get("planeta")}

    return digest


def _prepare_for_narrator(report: dict, genero: str = "masculino") -> dict:
    prefacio = _clean(report.get("prefacio", {}))
    capitulos_raw = report.get("capitulos", {})
    capitulos = {k: _clean(v) for k, v in capitulos_raw.items() if v is not None}
    return {"genero": genero, "prefacio": prefacio, "capitulos": capitulos}


_TIMEOUT = 120

_CAPS_LOTE_1 = {"cap1", "cap2", "cap3", "cap4", "cap5", "cap6"}
_CAPS_LOTE_2 = {"cap7", "cap10", "cap11"}


def _call_api(client: anthropic.Anthropic, payload: dict, instruction: str) -> dict:
    user_content = json.dumps(payload, ensure_ascii=False, indent=2)
    user_message = instruction + "\n\nDados:\n\n" + user_content
    response = client.messages.create(
        model=_MODEL,
        max_tokens=8192,
        timeout=_TIMEOUT,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )

    text = next((b.text for b in response.content if b.type == "text"), "")
    if "```" in text:
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else parts[0]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def generate_narrative(report_data: dict, genero: str = "masculino") -> dict:
    """Recebe dados brutos do relatório, retorna dict narrativo conforme schema canônico.

    3 lotes: cap1-6 | cap7+cap8_9+cap10-11 | prefácio+conclusão.
    Fallback gracioso: retorna {} se API_KEY ausente, timeout ou qualquer falha.
    Schema de output definido em Estrutura.md.
    """
    # DEV: narrator desativado durante desenvolvimento do frontend
    return {}

    try:
        client = _get_client()
        narrator_input = _prepare_for_narrator(report_data, genero=genero)
        caps = narrator_input.get("capitulos", {})
        prefacio_raw = narrator_input.get("prefacio", {})

        # Lote 1: cap1–6
        lote1_payload = {
            "genero": genero,
            "capitulos": {k: v for k, v in caps.items() if k in _CAPS_LOTE_1},
        }

        # Lote 2: cap7, cap8+cap9 merged, cap10–11
        lote2_caps: dict = {k: v for k, v in caps.items() if k in _CAPS_LOTE_2}
        lote2_caps["cap8_9"] = {
            "alquimia": caps.get("cap8", {}),
            "daimon": caps.get("cap9", {}),
        }
        lote2_payload = {
            "genero": genero,
            "contexto": {"id_dominante": prefacio_raw.get("id_dominante")},
            "capitulos": lote2_caps,
        }

        # Lote 3: prefácio + conclusão (digest compacto de todos os capítulos)
        digest = _build_digest(caps, prefacio_raw, genero)

        resultado1 = _call_api(client, lote1_payload, _INSTRUCAO_LOTE_1)
        resultado2 = _call_api(client, lote2_payload, _INSTRUCAO_LOTE_2)
        resultado3 = _call_api(client, digest, _INSTRUCAO_LOTE_3)

        return {
            "prefacio": resultado3.get("prefacio", ""),
            "conclusao": resultado3.get("conclusao", ""),
            "capitulos": {
                **resultado1.get("capitulos", {}),
                **resultado2.get("capitulos", {}),
            },
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Narrativa indisponível: %s: %s", type(exc).__name__, exc)
        return {}
