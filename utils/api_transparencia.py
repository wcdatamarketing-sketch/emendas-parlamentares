# ============================================================
# utils/api_transparencia.py
# Responsável por toda comunicação com a API do Portal da
# Transparência do Governo Federal
# ============================================================

# "import requests" traz a biblioteca que faz chamadas HTTP
# ou seja, ela permite que nosso código "navegue" em URLs
# assim como um navegador faz, mas de forma automática
import requests

# "time" é uma biblioteca nativa do Python (não precisa instalar)
# vamos usar ela para dar uma pausa entre as chamadas à API
# e respeitar o limite de requisições por minuto
import time


# ============================================================
# CONFIGURAÇÕES GERAIS
# ============================================================

# URL base da API — todo endpoint começa com esse endereço
# é como o "endereço da rua", e cada endpoint é o "número"
BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados"

# Tempo de pausa entre requisições (em segundos)
# A API aceita 90 requisições por minuto — 0.7s de pausa
# entre cada chamada garante que não vamos ultrapassar esse limite
PAUSA_ENTRE_REQUISICOES = 0.7


# ============================================================
# FUNÇÕES AUXILIARES (usadas internamente nesse arquivo)
# ============================================================

def _montar_cabecalho(api_key: str) -> dict:
    """
    Monta o cabeçalho HTTP que precisa ir em toda requisição.
    A API exige que a chave de acesso venha no cabeçalho,
    não na URL — é como um crachá que você apresenta na entrada.
    
    api_key: sua chave pessoal do Portal da Transparência
    retorna: dicionário com os campos do cabeçalho
    """
    return {
        "chave-api-dados": api_key,  # campo exigido pela API
        "Accept": "application/json", # dizemos que queremos resposta em JSON
    }


def _buscar_pagina(endpoint: str, parametros: dict, api_key: str) -> list:
    """
    Faz UMA requisição à API e retorna os dados recebidos.
    
    endpoint:   o caminho específico da API (ex: "/emendas-parlamentares")
    parametros: os filtros da busca (ex: ano, nome do autor)
    api_key:    sua chave de acesso
    retorna:    lista com os dados retornados pela API
    """
    
    # Monta a URL completa juntando a base com o endpoint
    # Exemplo: "https://api.portaldatransparencia.gov.br/api-de-dados/emendas-parlamentares"
    url_completa = f"{BASE_URL}{endpoint}"
    
    # Faz a requisição GET — é como digitar uma URL no navegador
    # "params" são os filtros que vão aparecer após o "?" na URL
    # "headers" é o cabeçalho com nossa chave de acesso
    resposta = requests.get(
        url_completa,
        params=parametros,
        headers=_montar_cabecalho(api_key),
        timeout=15,  # se não responder em 15 segundos, desiste
    )
    
    # Se a API retornou erro (ex: 401 sem autorização, 500 erro interno)
    # o raise_for_status() lança uma exceção e para a execução
    if resposta.status_code != 200:
        raise RuntimeError(
            f"Erro HTTP {resposta.status_code}: {resposta.text[:500]}"
        )
    
    # .json() converte o texto da resposta em uma lista Python
    # a API devolve texto no formato JSON, que parece com um dicionário
    dados = resposta.json()
    
    # Pausa para respeitar o limite de requisições da API
    time.sleep(PAUSA_ENTRE_REQUISICOES)
    
    # Se a API retornou algo, devolve — senão devolve lista vazia
    return dados if dados else []


def _buscar_todas_paginas(endpoint: str, parametros: dict, api_key: str, max_paginas: int = 20) -> list:
    """
    A API devolve no máximo 100 registros por vez (uma "página").
    Essa função fica pedindo página por página até acabar os dados.
    
    endpoint:    caminho da API
    parametros:  filtros da busca
    api_key:     chave de acesso
    max_paginas: limite de segurança para não ficar em loop infinito
    retorna:     lista completa com todos os registros encontrados
    """
    
    # Lista que vai acumular todos os resultados de todas as páginas
    todos_os_resultados = []
    
    # Fazemos uma cópia dos parâmetros para não modificar o original
    params = parametros.copy()
    
    # Começa pela página 1
    params["pagina"] = 1
    
    # Loop que vai repetir até acabar as páginas ou atingir o limite
    for numero_da_pagina in range(1, max_paginas + 1):
        
        # Atualiza o número da página nos parâmetros
        params["pagina"] = numero_da_pagina
        
        # Busca os dados dessa página
        dados_da_pagina = _buscar_pagina(endpoint, params, api_key)
        
        # Se a página veio vazia, significa que acabaram os dados
        if not dados_da_pagina:
            break  # sai do loop
        
        # Adiciona os resultados dessa página na lista geral
        # "extend" é diferente de "append": adiciona item por item
        # append adicionaria a lista inteira como um único item
        todos_os_resultados.extend(dados_da_pagina)
        
        # Se a página veio com menos de 100 itens, é a última
        # não precisa fazer mais uma requisição para confirmar
        if len(dados_da_pagina) < 100:
            break
    
    return todos_os_resultados


# ============================================================
# FUNÇÕES PÚBLICAS (usadas pelas telas do Streamlit)
# ============================================================

def buscar_emendas_por_autor(api_key: str, nome_autor: str, ano: int) -> list:
    """
    Busca todas as emendas de um parlamentar específico em um ano.
    Essa função será chamada na tela de Perfil do Parlamentar.
    
    api_key:    chave de acesso à API
    nome_autor: nome do deputado ou senador
    ano:        ano de referência (ex: 2024)
    retorna:    lista de emendas com todos os detalhes
    """
    
    # Monta os parâmetros de filtro que a API aceita
    parametros = {
        "nomeAutor": nome_autor,  # filtra pelo nome do parlamentar
        "ano": ano,               # filtra pelo ano
    }
    
    # Chama a função que pagina automaticamente e retorna tudo
    return _buscar_todas_paginas(
        endpoint="/emendas-parlamentares",
        parametros=parametros,
        api_key=api_key,
    )


def buscar_emendas_ranking(api_key: str, ano: int) -> list:
    """
    Busca emendas para montar o ranking geral da tela inicial.
    Retorna emendas de todos os parlamentares no ano informado.
    
    api_key: chave de acesso à API
    ano:     ano de referência
    retorna: lista de emendas para montar o ranking
    """
    
    parametros = {
        "ano": ano,
    }
    
    return _buscar_todas_paginas(
        endpoint="/emendas-parlamentares",
        parametros=parametros,
        api_key=api_key,
    )


def buscar_detalhe_emenda(api_key: str, codigo_emenda: str) -> dict:
    """
    Busca os detalhes completos de uma emenda específica.
    Será chamada quando o usuário clicar em uma emenda.
    
    api_key:        chave de acesso à API
    codigo_emenda:  código único da emenda
    retorna:        dicionário com todos os dados da emenda
    """
    
    # Esse endpoint retorna um único registro, não uma lista
    # por isso usamos _buscar_pagina diretamente (sem paginação)
    resultado = _buscar_pagina(
        endpoint=f"/emendas-parlamentares/{codigo_emenda}",
        parametros={},  # sem filtros adicionais — o código já identifica a emenda
        api_key=api_key,
    )
    
    # Retorna o primeiro item se existir, senão retorna dicionário vazio
    return resultado[0] if resultado else {}


def buscar_emendas_por_municipio(api_key: str, municipio: str, ano: int) -> list:
    """
    Busca emendas destinadas a um município específico.
    Será usada na tela de Busca por Recebedor.
    
    api_key:   chave de acesso à API
    municipio: nome do município
    ano:       ano de referência
    retorna:   lista de emendas destinadas ao município
    """
    
    parametros = {
        "municipioFavorecido": municipio,
        "ano": ano,
    }
    
    return _buscar_todas_paginas(
        endpoint="/emendas-parlamentares",
        parametros=parametros,
        api_key=api_key,
    )


def buscar_emendas_por_favorecido(api_key: str, nome_favorecido: str, ano: int) -> list:
    """
    Busca emendas recebidas por uma organização ou empresa específica.
    Será usada na tela de Busca por Recebedor.
    
    api_key:          chave de acesso à API
    nome_favorecido:  nome da ONG, empresa ou entidade
    ano:              ano de referência
    retorna:          lista de emendas recebidas pelo favorecido
    """
    
    parametros = {
        "nomeFavorecido": nome_favorecido,
        "ano": ano,
    }
    
    return _buscar_todas_paginas(
        endpoint="/emendas-parlamentares",
        parametros=parametros,
        api_key=api_key,
    )
