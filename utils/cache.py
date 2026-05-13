# ============================================================
# utils/cache.py
# Camada de cache entre as telas e as funções de dados.
#
# Regra geral: ttl=3600 (1 hora) para dados que mudam pouco.
# A lista de deputados da legislatura usa ttl=86400 (24h)
# pois muda muito raramente.
# ============================================================

import streamlit as st

from utils.data_loader import (
    carregar_emendas_ranking,
    carregar_emendas_por_autor,
    carregar_emendas_por_municipio,
    carregar_emendas_por_favorecido,
    carregar_detalhe_emenda,
    carregar_top_favorecidos,
)

from utils.api_camara import (
    buscar_deputados_legislatura,
    buscar_deputados,
    buscar_deputado_por_id,
    buscar_deputado_por_nome,
    buscar_partidos_legislatura,
    buscar_proposicoes_do_deputado,
    buscar_leis_aprovadas,
    buscar_relatorias_aprovadas,
    buscar_votacoes_do_deputado,
    buscar_votacoes_do_partido,
)


# ============================================================
# PORTAL DA TRANSPARÊNCIA (via data_loader)
# ============================================================

import datetime
_ANO_ATUAL = datetime.date.today().year

def _ttl_por_ano(ano: int) -> int:
    """7 dias para anos históricos, 1h para o ano atual."""
    return 604800 if ano < _ANO_ATUAL else 3600


@st.cache_data(ttl=604800)
def cache_emendas_por_autor(api_key: str, nome_autor: str, ano: int) -> list:
    return carregar_emendas_por_autor(api_key, nome_autor, ano)


@st.cache_data(ttl=604800)
def cache_emendas_ranking(api_key: str, ano: int) -> list:
    return carregar_emendas_ranking(api_key, ano)


@st.cache_data(ttl=86400)
def cache_detalhe_emenda(api_key: str, codigo_emenda: str) -> dict:
    return carregar_detalhe_emenda(api_key, codigo_emenda)


@st.cache_data(ttl=604800)
def cache_emendas_por_municipio(api_key: str, municipio: str, ano: int) -> list:
    return carregar_emendas_por_municipio(api_key, municipio, ano)


@st.cache_data(ttl=604800)
def cache_emendas_por_favorecido(api_key: str, nome_favorecido: str, ano: int) -> list:
    return carregar_emendas_por_favorecido(api_key, nome_favorecido, ano)


@st.cache_data(ttl=604800)
def cache_top_favorecidos(
    nome_autor: str = None,
    sigla_partido: str = None,
    anos: tuple = None,
    top_n: int = 10,
) -> list:
    """Top favorecidos por deputado ou partido. anos como tuple para ser hashável no cache."""
    return carregar_top_favorecidos(
        nome_autor=nome_autor,
        sigla_partido=sigla_partido,
        anos=list(anos) if anos else None,
        top_n=top_n,
    )


# ============================================================
# CÂMARA — DEPUTADOS
# ============================================================

@st.cache_data(ttl=86400)
def cache_deputados_legislatura(id_legislatura: int = 57) -> list:
    """
    Lista completa de deputados da legislatura.
    Usada para filtrar senadores da base CSV e popular selects.
    TTL de 24h pois a lista muda raramente.
    """
    return buscar_deputados_legislatura(id_legislatura)


@st.cache_data(ttl=86400)
def cache_partidos_legislatura(id_legislatura: int = 57) -> list:
    """
    Lista de siglas de partidos com deputados na legislatura.
    Usada para popular o select de partidos no Comparativo.
    """
    return buscar_partidos_legislatura(id_legislatura)


@st.cache_data(ttl=3600)
def cache_deputados(uf: str = None, partido: str = None) -> list:
    return buscar_deputados(uf, partido)


@st.cache_data(ttl=3600)
def cache_deputado_por_id(id_deputado: int) -> dict:
    return buscar_deputado_por_id(id_deputado)


@st.cache_data(ttl=3600)
def cache_deputado_por_nome(nome: str) -> list:
    return buscar_deputado_por_nome(nome)


# ============================================================
# CÂMARA — PROPOSIÇÕES E LEIS
# ============================================================

@st.cache_data(ttl=3600)
def cache_proposicoes_do_deputado(
    id_deputado: int,
    ano_inicio: int = 2023,
    ano_fim: int = 2026,
) -> list:
    return buscar_proposicoes_do_deputado(id_deputado, ano_inicio, ano_fim)


@st.cache_data(ttl=3600)
def cache_leis_aprovadas(
    id_deputado: int,
    ano_inicio: int = 2023,
    ano_fim: int = 2026,
) -> list:
    """Leis aprovadas onde o deputado foi AUTOR."""
    return buscar_leis_aprovadas(id_deputado, ano_inicio, ano_fim)


@st.cache_data(ttl=3600)
def cache_relatorias_aprovadas(
    id_deputado: int,
    ano_inicio: int = 2023,
    ano_fim: int = 2026,
) -> list:
    """Leis aprovadas onde o deputado foi RELATOR."""
    return buscar_relatorias_aprovadas(id_deputado, ano_inicio, ano_fim)


# ============================================================
# CÂMARA — VOTAÇÕES
# ============================================================

@st.cache_data(ttl=3600)
def cache_votacoes_do_deputado(
    id_deputado: int,
    ano_inicio: int = 2023,
    ano_fim: int = 2026,
) -> list:
    """Votações nominais de um deputado."""
    return buscar_votacoes_do_deputado(id_deputado, ano_inicio, ano_fim)


@st.cache_data(ttl=3600)
def cache_votacoes_do_partido(
    sigla_partido: str,
    id_legislatura: int = 57,
    ano_inicio: int = 2023,
    ano_fim: int = 2026,
) -> dict:
    """Votações agregadas de todos os deputados de um partido."""
    return buscar_votacoes_do_partido(
        sigla_partido, id_legislatura, ano_inicio, ano_fim
    )
