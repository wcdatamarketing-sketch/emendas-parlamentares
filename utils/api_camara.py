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

def _get(url: str, params: dict = None) -> dict:
    """
    Faz uma requisição GET e retorna o JSON completo.
    Aceita URL completa ou relativa ao BASE_URL.
    """
    # Se não começar com http, monta URL completa
    if not url.startswith("http"):
        url = f"{BASE_URL}{url}"
    resposta = requests.get(
        url,
        params=params,
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
            # URL completa da próxima página — passa sem params extras
            dados_json = _get(proxima_url)
        else:
            dados_json = _get(endpoint, params=params)

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
    Busca os votos nominais de um deputado usando os arquivos
    CSV anuais disponibilizados pela Câmara.

    URL: dadosabertos.camara.leg.br/arquivos/votacoesVotos/csv/votacoesVotos-{ano}.csv

    Cada linha do CSV contém o id do deputado e seu voto.
    Filtramos as linhas do deputado solicitado.

    Retorna lista de dicionários com tipoVoto e idVotacao.
    """
    import io
    import pandas as pd

    URL_CSV = (
        "https://dadosabertos.camara.leg.br/arquivos/votacoesVotos"
        "/csv/votacoesVotos-{ano}.csv"
    )

    votos_dep = []

    for ano in range(ano_inicio, ano_fim + 1):
        try:
            resp = requests.get(
                URL_CSV.format(ano=ano),
                timeout=60,
                headers={"Accept": "text/csv"},
            )
            resp.raise_for_status()

            df = pd.read_csv(
                io.BytesIO(resp.content),
                sep=";",
                encoding="utf-8",
                dtype=str,
                low_memory=False,
            )

            # Coluna com ID do deputado pode ser idDeputado ou deputado_id
            col_id = next(
                (c for c in df.columns if "idDeputado" in c or "deputado_id" in c.lower()),
                None,
            )
            col_voto = next(
                (c for c in df.columns if "tipoVoto" in c or "voto" in c.lower()),
                None,
            )

            if not col_id or not col_voto:
                continue

            df_dep = df[df[col_id].astype(str) == str(id_deputado)]

            for _, row in df_dep.iterrows():
                votos_dep.append({
                    "tipoVoto":   row.get(col_voto, ""),
                    "idVotacao":  row.get("idVotacao", row.get("id", "")),
                    "ano":        ano,
                })

            time.sleep(0.3)

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
    Agrega os votos de todos os deputados de um partido
    usando os CSVs anuais de votos da Câmara.

    Filtra diretamente pelo partido no CSV — muito mais rápido
    que iterar por deputado individualmente.
    """
    import io
    import pandas as pd

    URL_CSV = (
        "https://dadosabertos.camara.leg.br/arquivos/votacoesVotos"
        "/csv/votacoesVotos-{ano}.csv"
    )

    totais = {
        "total_sim":       0,
        "total_nao":       0,
        "total_abstencao": 0,
        "total_ausencia":  0,
        "total_votos":     0,
        "deputados":       0,
    }

    ids_dep = set()

    for ano in range(ano_inicio, ano_fim + 1):
        try:
            resp = requests.get(URL_CSV.format(ano=ano), timeout=60)
            resp.raise_for_status()

            df = pd.read_csv(
                io.BytesIO(resp.content),
                sep=";",
                encoding="utf-8",
                dtype=str,
                low_memory=False,
            )

            # Coluna de partido
            col_partido = next(
                (c for c in df.columns if "siglaPartido" in c or "partido" in c.lower()),
                None,
            )
            col_voto = next(
                (c for c in df.columns if "tipoVoto" in c or c.lower() == "voto"),
                None,
            )
            col_id = next(
                (c for c in df.columns if "idDeputado" in c or "deputado_id" in c.lower()),
                None,
            )

            if not col_partido or not col_voto:
                continue

            df_part = df[
                df[col_partido].str.upper() == sigla_partido.upper()
            ]

            if col_id is not None:
                ids_dep.update(df_part[col_id].dropna().unique())

            for voto in df_part[col_voto].str.upper().fillna(""):
                totais["total_votos"] += 1
                if voto == "SIM":
                    totais["total_sim"] += 1
                elif voto in ("NÃO", "NAO"):
                    totais["total_nao"] += 1
                elif voto in ("ABSTENÇÃO", "ABSTENCAO"):
                    totais["total_abstencao"] += 1
                else:
                    totais["total_ausencia"] += 1

            time.sleep(0.3)

        except Exception:
            continue

    totais["deputados"] = len(ids_dep) if ids_dep else totais["deputados"]
    return totais
