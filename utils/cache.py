# ============================================================
# utils/cache.py
# Camada de cache entre as telas e as funções de API
# Evita chamadas repetidas e respeita o limite da API
# ============================================================

# streamlit é importado aqui porque vamos usar o cache nativo dele
import streamlit as st

# Importamos as funções de busca dos dois arquivos que já criamos
# "from X import Y" significa: do arquivo X, traz apenas a função Y
from utils.api_transparencia import (
    buscar_emendas_por_autor,
    buscar_emendas_ranking,
    buscar_detalhe_emenda,
    buscar_emendas_por_municipio,
    buscar_emendas_por_favorecido,
)
from utils.api_camara import (
    buscar_deputados,
    buscar_deputado_por_id,
    buscar_proposicoes_do_deputado,
    buscar_deputado_por_nome,
)


# ============================================================
# O QUE É O @st.cache_data?
# ============================================================
# É um "decorador" — uma instrução colocada acima da função
# que adiciona comportamento extra a ela.
#
# Com @st.cache_data(ttl=3600):
# - Na primeira chamada: executa a função e guarda o resultado
# - Nas chamadas seguintes com os mesmos parâmetros: devolve
#   o resultado guardado sem chamar a API novamente
# - ttl=3600 significa "esqueça o cache após 3600 segundos (1 hora)"
#   após 1 hora, na próxima chamada busca dados frescos da API
# ============================================================


# ============================================================
# CACHE DAS FUNÇÕES DO PORTAL DA TRANSPARÊNCIA
# ============================================================

@st.cache_data(ttl=3600)
def cache_emendas_por_autor(api_key: str, nome_autor: str, ano: int) -> list:
    """
    Versão com cache da busca de emendas por autor.
    Se alguém buscar o mesmo parlamentar no mesmo ano,
    o resultado vem instantaneamente da memória.
    """
    return buscar_emendas_por_autor(api_key, nome_autor, ano)


@st.cache_data(ttl=3600)
def cache_emendas_ranking(api_key: str, ano: int) -> list:
    """
    Versão com cache do ranking geral.
    O ranking é o dado mais acessado — o cache aqui
    é especialmente importante para performance.
    """
    return buscar_emendas_ranking(api_key, ano)


@st.cache_data(ttl=3600)
def cache_detalhe_emenda(api_key: str, codigo_emenda: str) -> dict:
    """
    Versão com cache do detalhe de uma emenda específica.
    Detalhes de emenda raramente mudam — 1 hora de cache é seguro.
    """
    return buscar_detalhe_emenda(api_key, codigo_emenda)


@st.cache_data(ttl=3600)
def cache_emendas_por_municipio(api_key: str, municipio: str, ano: int) -> list:
    """
    Versão com cache da busca por município.
    """
    return buscar_emendas_por_municipio(api_key, municipio, ano)


@st.cache_data(ttl=3600)
def cache_emendas_por_favorecido(api_key: str, nome_favorecido: str, ano: int) -> list:
    """
    Versão com cache da busca por favorecido.
    """
    return buscar_emendas_por_favorecido(api_key, nome_favorecido, ano)


# ============================================================
# CACHE DAS FUNÇÕES DA CÂMARA
# ============================================================

@st.cache_data(ttl=3600)
def cache_deputados(uf: str = None, partido: str = None) -> list:
    """
    Versão com cache da lista de deputados.
    A lista de deputados muda muito pouco — cache de 1 hora é ideal.
    """
    return buscar_deputados(uf, partido)


@st.cache_data(ttl=3600)
def cache_deputado_por_id(id_deputado: int) -> dict:
    """
    Versão com cache dos detalhes de um deputado.
    """
    return buscar_deputado_por_id(id_deputado)


@st.cache_data(ttl=3600)
def cache_proposicoes_do_deputado(id_deputado: int, ano: int = None) -> list:
    """
    Versão com cache das proposições de um deputado.
    """
    return buscar_proposicoes_do_deputado(id_deputado, ano)


@st.cache_data(ttl=3600)
def cache_deputado_por_nome(nome: str) -> list:
    """
    Versão com cache da busca de deputado por nome.
    Útil para o campo de pesquisa — evita chamadas a cada letra digitada.
    """
    return buscar_deputado_por_nome(nome)
