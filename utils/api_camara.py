# ============================================================
# utils/api_camara.py
# Responsável por buscar dados da API de Dados Abertos
# da Câmara dos Deputados
# Documentação: https://dadosabertos.camara.leg.br/api/v2
# ============================================================

# requests para fazer as chamadas HTTP, igual ao arquivo anterior
import requests

# time para pausar entre requisições e não sobrecarregar a API
import time


# ============================================================
# CONFIGURAÇÕES GERAIS
# ============================================================

# URL base da API da Câmara — diferente da API do Portal da Transparência
# essa API é pública e não exige chave de acesso
BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

# Pausa entre requisições em segundos
# A API da Câmara não divulga limite oficial, mas 0.5s é uma boa prática
PAUSA_ENTRE_REQUISICOES = 0.5


# ============================================================
# FUNÇÕES AUXILIARES (internas do arquivo)
# ============================================================

def _buscar_pagina(endpoint: str, parametros: dict) -> dict:
    """
    Faz UMA requisição à API da Câmara e retorna a resposta completa.
    
    Diferente da API do Portal da Transparência, a API da Câmara
    devolve um dicionário com dois campos:
      - "dados": a lista de resultados
      - "links": links para próxima página, página anterior, etc.
    
    endpoint:   caminho específico da API (ex: "/deputados")
    parametros: filtros da busca
    retorna:    dicionário com "dados" e "links"
    """
    
    # Monta a URL completa
    url_completa = f"{BASE_URL}{endpoint}"
    
    # A API da Câmara não exige cabeçalho de autenticação
    # mas pedimos a resposta em JSON pelo cabeçalho Accept
    resposta = requests.get(
        url_completa,
        params=parametros,
        headers={"Accept": "application/json"},
        timeout=15,
    )
    
    # Lança erro se a API retornar código de erro
    resposta.raise_for_status()
    
    # Pausa para não sobrecarregar a API
    time.sleep(PAUSA_ENTRE_REQUISICOES)
    
    # Retorna o dicionário completo (com "dados" e "links")
    return resposta.json()


def _buscar_todas_paginas(endpoint: str, parametros: dict, max_paginas: int = 10) -> list:
    """
    Pagina automaticamente pelos resultados da API da Câmara.
    
    A API da Câmara usa um sistema diferente de paginação:
    em vez de número de página, ela devolve um link direto
    para a próxima página no campo "links".
    
    endpoint:    caminho da API
    parametros:  filtros da busca
    max_paginas: limite de segurança
    retorna:     lista completa com todos os registros
    """
    
    # Lista que vai acumular todos os resultados
    todos_os_resultados = []
    
    # Faz uma cópia dos parâmetros para não modificar o original
    params = parametros.copy()
    
    # Controla quantas páginas já buscamos
    paginas_buscadas = 0
    
    # URL da próxima página — começa com a URL do endpoint normal
    # e vai sendo atualizada conforme avançamos nas páginas
    proxima_url = f"{BASE_URL}{endpoint}"
    
    # Loop que continua enquanto houver próxima página
    while proxima_url and paginas_buscadas < max_paginas:
        
        # Faz a requisição para a URL atual
        resposta = requests.get(
            proxima_url,
            params=params if paginas_buscadas == 0 else {},
            # só manda os parâmetros na primeira página
            # nas páginas seguintes a URL já vem completa
            headers={"Accept": "application/json"},
            timeout=15,
        )
        resposta.raise_for_status()
        resultado = resposta.json()
        
        # Extrai a lista de dados do campo "dados"
        dados = resultado.get("dados", [])
        
        # Se veio vazio, acabaram os resultados
        if not dados:
            break
        
        # Adiciona os resultados dessa página na lista geral
        todos_os_resultados.extend(dados)
        paginas_buscadas += 1
        
        # Procura o link da próxima página no campo "links"
        # a API devolve uma lista de links com rel="next", "first", "last"
        proxima_url = None  # assume que não tem próxima
        for link in resultado.get("links", []):
            # "rel": "next" indica o link da próxima página
            if link.get("rel") == "next":
                proxima_url = link.get("href")
                break
        
        # Pausa entre requisições
        time.sleep(PAUSA_ENTRE_REQUISICOES)
    
    return todos_os_resultados


# ============================================================
# FUNÇÕES PÚBLICAS (usadas pelas telas do Streamlit)
# ============================================================

def buscar_deputados(uf: str = None, partido: str = None) -> list:
    """
    Busca a lista de deputados federais ativos.
    Pode filtrar por estado (UF) e/ou partido.
    Será usada no campo de busca e no ranking.
    
    uf:      sigla do estado (ex: "DF", "SP") — opcional
    partido: sigla do partido (ex: "PT", "PL") — opcional
    retorna: lista de deputados com nome, partido, UF e foto
    """
    
    # Monta os parâmetros — só inclui os que foram informados
    parametros = {
        "ordem": "ASC",       # ordem alfabética crescente
        "ordenarPor": "nome", # ordena pelo nome
    }
    
    # "if uf" só adiciona o parâmetro se o valor foi informado
    # evita mandar filtros vazios para a API
    if uf:
        parametros["siglaUf"] = uf
    if partido:
        parametros["siglaPartido"] = partido
    
    return _buscar_todas_paginas(
        endpoint="/deputados",
        parametros=parametros,
    )


def buscar_deputado_por_id(id_deputado: int) -> dict:
    """
    Busca os detalhes completos de um deputado pelo ID.
    Retorna informações como escolaridade, site, redes sociais.
    
    id_deputado: número identificador do deputado na API da Câmara
    retorna:     dicionário com todos os dados do deputado
    """
    
    resultado = _buscar_pagina(
        endpoint=f"/deputados/{id_deputado}",
        parametros={},
    )
    
    # O campo "dados" aqui é um dicionário único, não uma lista
    return resultado.get("dados", {})


def buscar_proposicoes_do_deputado(id_deputado: int, ano: int = None) -> list:
    """
    Busca os projetos de lei e outras proposições apresentadas
    por um deputado específico.
    Será usada na tela de Perfil do Parlamentar.
    
    id_deputado: ID do deputado na API da Câmara
    ano:         ano de referência — opcional
    retorna:     lista de proposições com ementa e status
    """
    
    parametros = {
        "ordem": "DESC",          # mais recentes primeiro
        "ordenarPor": "dataApresentacao",
    }
    
    # Adiciona filtro de ano se foi informado
    if ano:
        parametros["dataInicio"] = f"{ano}-01-01"  # formato exigido: AAAA-MM-DD
        parametros["dataFim"] = f"{ano}-12-31"
    
    return _buscar_todas_paginas(
        endpoint=f"/deputados/{id_deputado}/proposicoes",
        parametros=parametros,
    )


def buscar_deputado_por_nome(nome: str) -> list:
    """
    Busca deputados pelo nome — útil para o campo de pesquisa.
    Retorna todos os deputados cujo nome contém o texto buscado.
    
    nome:    texto para buscar no nome do deputado
    retorna: lista de deputados encontrados
    """
    
    parametros = {
        "nome": nome,         # a API filtra por parte do nome
        "ordem": "ASC",
        "ordenarPor": "nome",
    }
    
    return _buscar_todas_paginas(
        endpoint="/deputados",
        parametros=parametros,
    )
