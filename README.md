# Esoteric Calculation Engine

Motor de cálculo astronômico e esotérico que converte dados de nascimento em IDs via múltiplos sistemas de cálculo.

Este repositório contém exclusivamente o motor de cálculo, publicado para conformidade com a licença AGPL v3 do Swiss Ephemeris.

## Licença

Este projeto é distribuído sob a licença **GNU Affero General Public License v3.0 (AGPL-3.0)**, em conformidade com a licença dual do [Swiss Ephemeris](https://www.astro.com/swisseph/swephinfo_e.htm) (Astrodienst AG).

O código é fornecido **"como está"**, sem garantias de qualquer tipo. Não oferecemos suporte técnico para uso externo.

## Stack

- Python 3.12 + FastAPI
- [pyswisseph](https://pypi.org/project/pyswisseph/) — binding Python para o Swiss Ephemeris
- Swiss Ephemeris data files (`.se1`) — arquivos de efemérida do [Swiss Ephemeris](https://www.astro.com/swisseph/)
