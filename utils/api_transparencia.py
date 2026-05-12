# ============================================================
# utils/api_transparencia.py
# Comunicação com a API do Portal da Transparência
# ============================================================

import requests
import time

BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados"
PAUSA_ENTRE_REQUISICOES = 0.7


def _buscar_pagina(endpoint: str, parametros: dict, api_key: str) -> list:
    """Faz UMA requisição à API e retorna os dados recebidos."""
    
    url_completa = f"{BASE_URL}{endpoint}"
    
    cabecalho = {
        "chave-api-dados": api_key.strip(),
        "Accept": "application/json",
    }
    
    resposta = requests.get(
        url_completa,
        params=parametros,
        headers=cabecalho,
        timeout=15,
    )
    
    if resposta.status_code != 200:
        raise RuntimeError(
            f"Erro HTTP {resposta.status_code}: {resposta.text[:300]}"
        )
    
    dados = resposta.json()
    time.sleep(PAUSA_ENTRE_REQUISICOES)
    return dados if dados else []


def _buscar_todas_paginas(endpoint: str, parametros: dict, api_key: str, max_paginas: int = 20) -> list:
    """Pagina automaticamente até acabar os dados."""
    
    todos_os_resultados = []
    params = parametros.copy()
    
    for numero_da_pagina in range(1, max_paginas + 1):
        params["pagina"] = numero_da_pagina
        dados_da_pagina = _buscar_pagina(endpoint, params, api_key)
        
        if not dados_da_pagina:
            break
        
        todos_os_resultados.extend(dados_da_pagina)
        
        # A API retorna 15 itens por página por padrão
        # Se veio menos de 15, é a última página
        if len(dados_da_pagina) < 15:
            break
    
    return todos_os_resultados

# ============================================================
# FUNÇÕES PÚBLICAS
# ============================================================

def buscar_emendas_por_autor(api_key: str, nome_autor: str, ano: int) -> list:
    """Busca emendas de um parlamentar específico em um ano."""
    parametros = {
        "nomeAutor": nome_autor,
        "ano": ano,
    }
    return _buscar_todas_paginas("/emendas", parametros, api_key)


def buscar_emendas_ranking(api_key: str, ano: int) -> list:
    """Busca emendas para o ranking geral."""
    parametros = {
        "ano": ano,
    }
    return _buscar_todas_paginas("/emendas", parametros, api_key)


def buscar_detalhe_emenda(api_key: str, codigo_emenda: str) -> dict:
    """Busca detalhes de uma emenda pelo código."""
    parametros = {"codigoEmenda": codigo_emenda}
    resultado = _buscar_todas_paginas("/emendas", parametros, api_key)
    return resultado[0] if resultado else {}


def buscar_emendas_por_municipio(api_key: str, municipio: str, ano: int) -> list:
    """Busca emendas destinadas a um município."""
    parametros = {
        "municipioBeneficiario": municipio,
        "ano": ano,
    }
    return _buscar_todas_paginas("/emendas", parametros, api_key)


def buscar_emendas_por_favorecido(api_key: str, nome_favorecido: str, ano: int) -> list:
    """Busca emendas por nome do favorecido."""
    parametros = {
        "nomeBeneficiario": nome_favorecido,
        "ano": ano,
    }
    return _buscar_todas_paginas("/emendas", parametros, api_key)
