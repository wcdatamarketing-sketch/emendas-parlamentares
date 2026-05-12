# ============================================================
# utils/cache.py
# Camada de cache entre as telas e as funções de dados.
#
# ATUALIZAÇÃO: agora chama o data_loader.py em vez da API
# diretamente. O data_loader decide automaticamente se usa
# os CSVs do Google Drive ou cai na API como fallback.
# ============================================================

import streamlit as st

# Importamos do data_loader — ele centraliza toda a lógica de dados
from utils.data_loader import (
    carregar_emendas_ranking,
    carregar_emendas_por_autor,
    carregar_emendas_por_municipio,
    carregar_emendas_por_favorecido,
    carregar_detalhe_emenda,
)

# A API da Câmara não muda — continua sendo chamada diretamente
from utils.api_camara import (
    buscar_deputados,
    buscar_deputado_por_id,
    buscar_proposicoes_do_deputado,
    buscar_deputado_por_nome,
)


# ============================================================
# CACHE — PORTAL DA TRANSPARÊNCIA (via data_loader)
# ============================================================

@st.cache_data(ttl=3600)
def cache_emendas_por_autor(api_key: str, nome_autor: str, ano: int) -> list:
    return carregar_emendas_por_autor(api_key, nome_autor, ano)


@st.cache_data(ttl=3600)
def cache_emendas_ranking(api_key: str, ano: int) -> list:
    return carregar_emendas_ranking(api_key, ano)


@st.cache_data(ttl=3600)
def cache_detalhe_emenda(api_key: str, codigo_emenda: str) -> dict:
    return carregar_detalhe_emenda(api_key, codigo_emenda)


@st.cache_data(ttl=3600)
def cache_emendas_por_municipio(api_key: str, municipio: str, ano: int) -> list:
    return carregar_emendas_por_municipio(api_key, municipio, ano)


@st.cache_data(ttl=3600)
def cache_emendas_por_favorecido(api_key: str, nome_favorecido: str, ano: int) -> list:
    return carregar_emendas_por_favorecido(api_key, nome_favorecido, ano)


# ============================================================
# CACHE — CÂMARA DOS DEPUTADOS (sem alteração)
# ============================================================

@st.cache_data(ttl=3600)
def cache_deputados(uf: str = None, partido: str = None) -> list:
    return buscar_deputados(uf, partido)


@st.cache_data(ttl=3600)
def cache_deputado_por_id(id_deputado: int) -> dict:
    return buscar_deputado_por_id(id_deputado)


@st.cache_data(ttl=3600)
def cache_proposicoes_do_deputado(id_deputado: int, ano: int = None) -> list:
    return buscar_proposicoes_do_deputado(id_deputado, ano)


@st.cache_data(ttl=3600)
def cache_deputado_por_nome(nome: str) -> list:
    return buscar_deputado_por_nome(nome)
