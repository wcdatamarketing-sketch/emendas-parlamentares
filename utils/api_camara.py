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
    Busca todas as proposições apresentadas por um deputado
    no período informado.

    id_deputado: ID do deputado na API da Câmara
    ano_inicio:  primeiro ano do período (padrão: 2023)
    ano_fim:     último ano do período (padrão: 2026)
    retorna:     lista de proposições com tipo, número, ementa e data
    """
    return _paginar(
        f"/deputados/{id_deputado}/proposicoes",
        {
            "dataInicio": f"{ano_inicio}-01-01",
            "dataFim":    f"{ano_fim}-12-31",
            "ordenarPor": "dataApresentacao",
            "ordem":      "DESC",
            "itens":      100,
        },
        max_paginas=20,
    )


def buscar_leis_aprovadas(
    id_deputado: int,
    ano_inicio: int = 2023,
    ano_fim: int = 2026,
) -> list:
    """
    Busca proposições do deputado que foram aprovadas e
    transformadas em norma jurídica (viraram lei).

    Filtra por:
    - Tipos legislativos que podem virar lei: PL, PLP, PEC, MPV
    - Situação: "Transformada em norma jurídica" (codSituacao=1140)
      ou tramitação encerrada com aprovação

    id_deputado: ID do deputado
    retorna:     lista de leis com ementa, número e data de aprovação
    """
    # Busca todas as proposições do deputado no período
    todas = buscar_proposicoes_do_deputado(id_deputado, ano_inicio, ano_fim)

    # Filtra apenas os tipos que podem se tornar leis
    tipos_lei = {"PL", "PLP", "PEC", "MPV", "PDL", "PDS"}

    leis = []
    for prop in todas:
        tipo = prop.get("siglaTipo", "")
        if tipo not in tipos_lei:
            continue

        # Verifica o status de tramitação
        # A API retorna statusProposicao com descricaoSituacao
        situacao = prop.get("statusProposicao", {})
        desc_situacao = situacao.get("descricaoSituacao", "").lower()

        if any(termo in desc_situacao for termo in [
            "transformada em norma",
            "transformado em norma",
            "lei ordinária",
            "lei complementar",
            "promulgada",
            "sancionada",
        ]):
            leis.append(prop)

    return leis


def buscar_relatorias_aprovadas(
    id_deputado: int,
    ano_inicio: int = 2023,
    ano_fim: int = 2026,
) -> list:
    """
    Busca proposições onde o deputado atuou como RELATOR
    e que foram aprovadas.

    A API da Câmara tem endpoint específico para relatorias:
    /deputados/{id}/relatores

    id_deputado: ID do deputado
    retorna:     lista de relatorias com ementa e resultado
    """
    try:
        relatorias = _paginar(
            f"/deputados/{id_deputado}/relatores",
            {
                "dataInicio": f"{ano_inicio}-01-01",
                "dataFim":    f"{ano_fim}-12-31",
                "itens":      100,
            },
            max_paginas=10,
        )
    except Exception:
        # Endpoint pode não existir para todos os deputados
        return []

    # Filtra apenas as que foram aprovadas
    aprovadas = []
    for r in relatorias:
        situacao = r.get("descricaoSituacao", "").lower()
        if any(termo in situacao for termo in [
            "aprovad", "transformad", "promulgad", "sancionad"
        ]):
            aprovadas.append(r)

    return aprovadas


# ============================================================
# VOTAÇÕES
# ============================================================

def buscar_votacoes_do_deputado(
    id_deputado: int,
    ano_inicio: int = 2023,
    ano_fim: int = 2026,
) -> list:
    """
    Busca como o deputado votou nas votações nominais do plenário.

    Retorna lista com cada votação: proposta, data e voto do deputado
    (Sim, Não, Abstenção, Obstrução, Artigo 17, etc.)

    id_deputado: ID do deputado
    retorna:     lista de votos individuais
    """
    return _paginar(
        f"/deputados/{id_deputado}/votos",
        {
            "dataInicio": f"{ano_inicio}-01-01",
            "dataFim":    f"{ano_fim}-12-31",
            "itens":      100,
        },
        max_paginas=30,
    )


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
