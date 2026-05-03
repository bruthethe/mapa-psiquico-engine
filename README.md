# Mapa Psíquico — Motor de Cálculo

Motor de cálculo astronômico e esotérico do projeto **Mapa Psíquico**.

Este repositório contém os motores de cálculo que convertem data, hora e local de nascimento em IDs arquetípicos, cruzando 15 sistemas simbólicos: astrologia tropical, védica, Ba Zi, Tzolkin, Human Design, horas planetárias caldeias e outros.

## Licença

Este projeto é distribuído sob a licença **GNU Affero General Public License v3.0 (AGPL-3.0)**, em conformidade com a licença dual do [Swiss Ephemeris](https://www.astro.com/swisseph/swephinfo_e.htm) (Astrodienst AG).

O código é fornecido **"como está"**, sem garantias de qualquer tipo. Não oferecemos suporte técnico para uso externo.

## Repositório principal

O produto completo (incluindo dados proprietários de arquétipos, traduções e interface) é desenvolvido em repositório privado separado. Este repositório existe exclusivamente para satisfazer os requisitos de licenciamento AGPL do Swiss Ephemeris.

## Stack

- Python 3.12 + FastAPI
- [pyswisseph](https://pypi.org/project/pyswisseph/) — binding Python para o Swiss Ephemeris
- Swiss Ephemeris data files (`.se1`) — arquivos de efemérida incluídos em `../data/ephemeris/`
