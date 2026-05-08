"""Renderer de relatório em plain text para o formulário de testes (6.3)."""

from __future__ import annotations

_CAP_TITLES = {
    "cap1":  "CAP. 1  — ARQUÉTIPO CENTRAL",
    "cap2":  "CAP. 2  — ASTROLOGIA TROPICAL",
    "cap3":  "CAP. 3  — ASTROLOGIA VÉDICA",
    "cap4":  "CAP. 4  — BA ZI",
    "cap5":  "CAP. 5  — TZOLKIN MAYA",
    "cap6":  "CAP. 6  — NUMEROLOGIA",
    "cap7":  "CAP. 7  — TARÔ E I CHING",
    "cap8":  "CAP. 8  — ALQUIMIA",
    "cap9":  "CAP. 9  — DAIMON DA HORA",
    "cap10": "CAP. 10 — HUMAN DESIGN",
    "cap11": "CAP. 11 — PANTEÕES",
    "cap12": "CAP. 12 — MATERIALIZAÇÃO SENSORIAL",
}

_LABEL_MAP = {
    "id_dominante": "ID Dominante",
    "id_dominante_b": "ID Dominante B",
    "status": "Status",
    "master_label": "Label Mestre",
    "master_label_b": "Label Mestre B",
    "titulo": "Título",
    "texto": "Texto",
    "id_dados": "ID Dados",
    "essencia_solar": "Essência Solar",
    "mascara": "Máscara",
    "refugio_lunar": "Refúgio Lunar",
    "necessidade": "Necessidade",
    "demonio": "Demônio (Sombra)",
    "arquetipos": "Arquétipos",
    "arquetipos_b": "Arquétipos B",
    "goetia": "Sombra Goética",
    "goetia_b": "Sombra Goética B",
    "planet": "Planeta",
    "sign": "Signo",
    "sign_b": "Signo B",
    "id_gatilho": "ID Gatilho",
    "id_gatilho_b": "ID Gatilho B",
    "temperamentos": "Temperamentos",
    "temperamentos_b": "Temperamentos B",
    "elemento_dominante": "Elemento Dominante",
    "elemento_secundario": "Elemento Secundário",
    "temperamento_dominante": "Temperamento Dominante",
    "temperamento_secundario": "Temperamento Secundário",
    "pontuacao": "Pontuação",
    "sol": "Sol",
    "lua": "Lua",
    "ascendente": "Ascendente",
    "planetas": "Planetas",
    "nakshatra": "Nakshatra",
    "atmakaraka": "Atmakaraka",
    "purushartha": "Purushartha",
    "nome": "Nome",
    "nome_b": "Nome B",
    "regente": "Regente",
    "pada": "Pada",
    "pada_b": "Pada B",
    "simbolo": "Símbolo",
    "deidade": "Deidade",
    "qualidade": "Qualidade",
    "graha": "Graha",
    "grau_no_signo": "Grau no Signo",
    "ano": "Pilar do Ano",
    "mes": "Pilar do Mês",
    "dia": "Pilar do Dia",
    "hora": "Pilar da Hora",
    "animal": "Animal",
    "animal_b": "Animal B",
    "elemento": "Elemento",
    "elemento_b": "Elemento B",
    "kin": "Kin",
    "selo": "Selo",
    "tom": "Tom",
    "oraculo": "Oráculo",
    "pitagorica": "Pitagórica",
    "cabalistica": "Cabalística",
    "caldeia": "Caldeia",
    "gematria": "Gematria",
    "taro": "Tarô",
    "iching": "I Ching",
    "signo_solar": "Signo Solar",
    "fase": "Fase Alquímica",
    "operacao": "Operação",
    "vibe": "Vibe",
    "planeta": "Planeta",
    "planeta_b": "Planeta B",
    "numero_hora": "Nº da Hora",
    "numero_hora_b": "Nº da Hora B",
    "periodo": "Período",
    "periodo_b": "Período B",
    "tipo": "Tipo",
    "tipo_b": "Tipo B",
    "estrategia": "Estratégia",
    "estrategia_b": "Estratégia B",
    "tipo_id_gatilho": "ID Tipo",
    "tipo_b_id_gatilho": "ID Tipo B",
    "autoridade": "Autoridade",
    "autoridade_id_gatilho": "ID Autoridade",
    "centros_definidos": "Centros Definidos",
    "canais_ativos": "Canais Ativos",
    "porta_sol_personalidade": "Porta Sol (Personalidade)",
    "porta_sol_personalidade_b": "Porta Sol B",
    "personalidade": "Ativações Personalidade",
    "design": "Ativações Design",
    "chakra": "Chakra",
    "sistema": "Sistema Biológico",
    "frequencia": "Frequência (Hz)",
    "panteoes": "Panteões",
    "panteoes_b": "Panteões B",
    "divindades": "Divindades",
    "materializacao": "Materialização",
    "materializacao_b": "Materialização B",
    "cores": "Cores",
    "metais": "Metais",
    "cristais": "Cristais",
    "ervas": "Ervas",
    "notas": "Notas Musicais",
    "geometria": "Geometria Sagrada",
    "animais": "Animais",
    "terra": "Terra",
    "agua": "Água",
    "ar": "Ar",
    "criaturas": "Criaturas Míticas",
    "vote": "Voto",
    "overall_status": "Status Temporal",
    "index": "Índice",
}


def _label(key: str) -> str:
    return _LABEL_MAP.get(key, key.replace("_", " ").title())


def _sep(title: str) -> str:
    return f"\n{'=' * 60}\n{title}\n{'=' * 60}"


def _val(v: object) -> str:
    if v is None:
        return "—"
    if isinstance(v, list):
        if not v:
            return "—"
        if isinstance(v[0], (list, tuple)):
            return "  " + ", ".join(f"({a}-{b})" for a, b in v)
        return ", ".join(str(i) for i in v)
    return str(v)


def _render_dict(d: dict, indent: int = 0) -> list[str]:
    """Converte dict recursivamente em linhas `Label: valor`."""
    lines: list[str] = []
    pad = "  " * indent
    for k, v in d.items():
        lbl = _label(k)
        if isinstance(v, dict):
            lines.append(f"{pad}{lbl}:")
            lines.extend(_render_dict(v, indent + 1))
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            lines.append(f"{pad}{lbl}:")
            for i, item in enumerate(v, 1):
                lines.append(f"{pad}  [{i}]")
                lines.extend(_render_dict(item, indent + 2))
        else:
            lines.append(f"{pad}{lbl}: {_val(v)}")
    return lines


def _render_prefacio(report: dict) -> list[str]:
    lines: list[str] = []
    c = report["consolidation"]
    pref = report["prefacio"]

    if c.get("id_dominante_b") is not None:
        lines.append(f"Status: HÍBRIDO (Frequência em Transição)")
        lines.append(
            f"ID Dominante: {c['id_dominante']} | {c['id_dominante_b']}"
        )
    else:
        lines.append(f"Status: {pref.get('status', '—')}")
        lines.append(f"ID Dominante: {c['id_dominante']}")

    ml = pref.get("master_label")
    if ml:
        lines.append(f"Label Mestre: {ml['titulo']} — {ml['texto']}")

    ml_b = pref.get("master_label_b")
    if ml_b:
        lines.append(f"Label Mestre B: {ml_b['titulo']} — {ml_b['texto']}")

    return lines


def render_plain_text(report: dict) -> str:
    out: list[str] = []

    out.append(_sep("PREFÁCIO"))
    out.extend(_render_prefacio(report))

    for cap_key, title in _CAP_TITLES.items():
        cap_data = report["capitulos"].get(cap_key)
        if cap_data is None:
            continue
        out.append(_sep(title))
        out.extend(_render_dict(cap_data))

    out.append(f"\n{'=' * 60}")
    out.append("VOTOS (debug)")
    out.append(f"{'=' * 60}")
    dbg = report.get("debug", {})
    out.append(f"Fase 1:   {dbg.get('votes_fase1')}")
    out.append(f"Fase 2:   {dbg.get('votes_fase2')}")
    out.append(f"Fase 1-B: {dbg.get('votes_fase1_b')}")
    out.append(f"Timezone: {dbg.get('tz_name')}  Lat: {dbg.get('lat')}  Lon: {dbg.get('lon')}")

    return "\n".join(out)
