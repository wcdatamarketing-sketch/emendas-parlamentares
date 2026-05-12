# ============================================================
# utils/api_camara.py
# Comunicação com a API de Dados Abertos da Câmara dos Deputados
# Documentação: https://dadosabertos.camara.leg.br/api/v2
#
# FUNÇÕES DISPONÍVEIS:
#
# --- Deputados ---
# buscar_deputados_legislatura()  → lista completa da 57ª legislatura
# buscar_deputados()              → lista com filtros opcionais
# buscar_deputado_por_id()        → detalhes de um deputado
# buscar_deputado_por_nome()      → busca por nome parcial
# buscar_partidos_legislatura()   → lista de partidos com deputados ativos
#
# --- Proposições e Leis ---
# buscar_proposicoes_do_deputado()  → todas as proposições
# buscar_leis_aprovadas()           → PLs aprovados que viraram lei
#                                     onde o deputado foi autor ou relator
#
# --- Votações ---
# buscar_votacoes_do_deputado()     → como o deputado votou (nominais)
# buscar_votacoes_do_partido()      → votos agregados de um partido
# ============================================================

import requests
import time


# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
PAUSA_ENTRE_REQUISICOES = 0.5

# 57ª Legislatura = 2023-2027
ID_LEGISLATURA_ATUAL = 57


# ============================================================
# FUNÇÕES INTERNAS
# ============================================================

def _get(endpoint: str, params: dict = None, url_completa: str = None) -> dict:
    """
    Faz uma requisição GET e retorna o JSON completo.
    Aceita endpoint relativo ou URL completa (para paginação).
    """
    url = url_completa or f"{BASE_URL}{endpoint}"
    resposta = requests.get(
        url,
        params=params if not url_completa else None,
        headers={"Accept": "application/json"},
        timeout=20,
    )
    resposta.raise_for_status()
    time.sleep(PAUSA_ENTRE_REQUISICOES)
    return resposta.json()


def _paginar(endpoint: str, params: dict, max_paginas: int = 20) -> list:
    """
    Busca todas as páginas de um endpoint paginado.
    Segue o link "next" retornado pela API até acabar.
    """
    resultados = []
    proxima_url = None
    pagina = 0

    while pagina < max_paginas:
        if proxima_url:
            dados_json = _get(endpoint="", url_completa=proxima_url)
        else:
            dados_json = _get(endpoint=endpoint, params=params)

        dados = dados_json.get("dados", [])
        if not dados:
            break

        resultados.extend(dados)
        pagina += 1

        proxima_url = None
        for link in dados_json.get("links", []):
            if link.get("rel") == "next":
                proxima_url = link.get("href")
                break

        if not proxima_url:
            break

    return resultados


# ============================================================
# DEPUTADOS
# ============================================================

def buscar_deputados_legislatura(id_legislatura: int = ID_LEGISLATURA_ATUAL) -> list:
    """
    Retorna a lista COMPLETA de deputados de uma legislatura.
    Usada para filtrar a base CSV (remover senadores e outros).
    Também alimenta os selects da tela de Comparativo.

    id_legislatura: número da legislatura (padrão: 57 = 2023-2027)
    retorna: lista com id, nome, partido, UF de cada deputado
    """
    return _paginar(
        endpoint="/deputados",
        params={
            "idLegislatura": id_legislatura,
            "ordenarPor": "nome",
            "ordem": "ASC",
            "itens": 100,
        },
        max_paginas=10,
    )


def buscar_deputados(uf: str = None, partido: str = None) -> list:
    """
    Lista deputados ativos com filtros opcionais de UF e partido.
    """
    params = {"ordenarPor": "nome", "ordem": "ASC", "itens": 100}
    if uf:
        params["siglaUf"] = uf
    if partido:
        params["siglaPartido"] = partido
    return _paginar("/deputados", params)


def buscar_deputado_por_id(id_deputado: int) -> dict:
    """
    Detalhes completos de um deputado pelo ID.
    Retorna nome, partido, UF, foto, escolaridade, site etc.
    """
    resultado = _get(f"/deputados/{id_deputado}")
    return resultado.get("dados", {})


def buscar_deputado_por_nome(nome: str) -> list:
    """
    Busca deputados pelo nome (parcial).
    Usada como fallback quando não temos o ID.
    """
    return _paginar(
        "/deputados",
        {"nome": nome, "ordenarPor": "nome", "ordem": "ASC"},
    )


def buscar_partidos_legislatura(id_legislatura: int = ID_LEGISLATURA_ATUAL) -> list:
    """
    Retorna a lista de partidos que têm deputados na legislatura.
    Usada para popular o select de partidos no Comparativo.

    Retorna lista de strings com as siglas dos partidos,
    ordenada alfabeticamente.
    """
    deputados = buscar_deputados_legislatura(id_legislatura)
    partidos = sorted(set(
        d.get("siglaPartido", "")
        for d in deputados
        if d.get("siglaPartido")
    ))
    return partidos


# ============================================================
# PROPOSIÇÕES E LEIS
# ============================================================

def buscar_proposicoes_do_deputado(
    id_deputado: int,
    ano_inicio: int = 2023,
    ano_fim: int = 2026,
) -> list:
    """
    Busca todas as proposições apresentadas por um deputado.
    Endpoint correto: /proposicoes?idDeputadoAutor={id}
    (não existe /deputados/{id}/proposicoes)
    """
    return _paginar(
        "/proposicoes",
        {
            "idDeputadoAutor": id_deputado,
            "dataInicio":      f"{ano_inicio}-01-01",
            "dataFim":         f"{ano_fim}-12-31",
            "ordenarPor":      "dataApresentacao",
            "ordem":           "DESC",
            "itens":           100,
        },
        max_paginas=20,
    )


def buscar_leis_aprovadas(
    id_deputado: int,
    ano_inicio: int = 2023,
    ano_fim: int = 2026,
) -> list:
    """
    Busca proposições do deputado que viraram lei.
    Usa codSituacao=1140 que é o código de "Transformada em norma jurídica"
    na API da Câmara.
    """
    # Tipos que podem virar lei
    tipos_lei = ["PL", "PLP", "PEC", "MPV", "PDL", "PDS"]
    leis = []

    for tipo in tipos_lei:
        try:
            resultado = _paginar(
                "/proposicoes",
                {
                    "idDeputadoAutor": id_deputado,
                    "siglaTipo":       tipo,
                    "codSituacao":     1140,   # Transformada em norma jurídica
                    "dataInicio":      f"{ano_inicio}-01-01",
                    "dataFim":         f"{ano_fim}-12-31",
                    "itens":           100,
                },
                max_paginas=5,
            )
            leis.extend(resultado)
        except Exception:
            continue

    return leis


def buscar_relatorias_aprovadas(
    id_deputado: int,
    ano_inicio: int = 2023,
    ano_fim: int = 2026,
) -> list:
    """
    Busca proposições onde o deputado foi RELATOR e que viraram lei.
    Endpoint: /proposicoes?idRelator={id}&codSituacao=1140
    """
    tipos_lei = ["PL", "PLP", "PEC", "MPV", "PDL", "PDS"]
    relatorias = []

    for tipo in tipos_lei:
        try:
            resultado = _paginar(
                "/proposicoes",
                {
                    "idRelator":   id_deputado,
                    "siglaTipo":   tipo,
                    "codSituacao": 1140,
                    "dataInicio":  f"{ano_inicio}-01-01",
                    "dataFim":     f"{ano_fim}-12-31",
                    "itens":       100,
                },
                max_paginas=5,
            )
            relatorias.extend(resultado)
        except Exception:
            continue

    return relatorias


# ============================================================
# VOTAÇÕES
# ============================================================

def buscar_votacoes_do_deputado(
    id_deputado: int,
    ano_inicio: int = 2023,
    ano_fim: int = 2026,
) -> list:
    """
    Busca como o deputado votou nas votações nominais.
    Endpoint correto: /votacoes com filtro de data,
    depois busca os votos de cada votação que contém o deputado.

    Estratégia mais simples e que funciona na API v2:
    busca /votacoes no período e para cada uma pega os votos
    filtrando pelo deputado.

    Para evitar timeout, limita a 200 votações no período.
    """
    # Passo 1: lista as votações do período
    votacoes = _paginar(
        "/votacoes",
        {
            "dataInicio": f"{ano_inicio}-01-01",
            "dataFim":    f"{ano_fim}-12-31",
            "ordenarPor": "dataHoraRegistro",
            "ordem":      "DESC",
            "itens":      100,
        },
        max_paginas=2,   # limita a ~200 votações para não travar
    )

    votos_dep = []

    # Passo 2: para cada votação, busca os votos e filtra pelo deputado
    for votacao in votacoes:
        id_votacao = votacao.get("id")
        if not id_votacao:
            continue
        try:
            votos = _get(f"/votacoes/{id_votacao}/votos").get("dados", [])
            for voto in votos:
                dep = voto.get("deputado_", {})
                if str(dep.get("id", "")) == str(id_deputado):
                    # Enriquece com dados da votação
                    voto["idVotacao"]    = id_votacao
                    voto["dataVotacao"]  = votacao.get("dataHoraRegistro", "")
                    voto["descricao"]    = votacao.get("descricao", "")
                    votos_dep.append(voto)
                    break
        except Exception:
            continue

    return votos_dep


def buscar_votacoes_do_partido(
    sigla_partido: str,
    id_legislatura: int = ID_LEGISLATURA_ATUAL,
    ano_inicio: int = 2023,
    ano_fim: int = 2026,
) -> dict:
    """
    Agrega os votos de TODOS os deputados de um partido.

    Para cada votação nominal, conta quantos deputados votaram
    Sim, Não, Abstenção etc.

    sigla_partido:  sigla do partido (ex: "PT", "PL")
    retorna:        dicionário com totais agregados:
                    {
                        "total_sim": N,
                        "total_nao": N,
                        "total_abstencao": N,
                        "total_ausencia": N,
                        "total_votos": N,
                        "deputados": N,
                    }
    """
    # Busca todos os deputados do partido na legislatura
    deputados = _paginar(
        "/deputados",
        {
            "idLegislatura": id_legislatura,
            "siglaPartido":  sigla_partido,
            "ordenarPor":    "nome",
            "itens":         100,
        },
    )

    if not deputados:
        return {}

    # Agrega os votos de todos os deputados do partido
    totais = {
        "total_sim":       0,
        "total_nao":       0,
        "total_abstencao": 0,
        "total_ausencia":  0,
        "total_votos":     0,
        "deputados":       len(deputados),
    }

    for dep in deputados:
        id_dep = dep.get("id")
        if not id_dep:
            continue
        try:
            votos = buscar_votacoes_do_deputado(id_dep, ano_inicio, ano_fim)
            for voto in votos:
                tipo_voto = voto.get("tipoVoto", "").strip().upper()
                totais["total_votos"] += 1
                if tipo_voto == "SIM":
                    totais["total_sim"] += 1
                elif tipo_voto == "NÃO" or tipo_voto == "NAO":
                    totais["total_nao"] += 1
                elif tipo_voto in ("ABSTENÇÃO", "ABSTENCAO"):
                    totais["total_abstencao"] += 1
                else:
                    totais["total_ausencia"] += 1
        except Exception:
            continue

    return totais
