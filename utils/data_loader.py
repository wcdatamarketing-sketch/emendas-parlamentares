# ============================================================
# utils/data_loader.py
#
# CAMADA DE DADOS UNIFICADA — Google Drive + API fallback
#
# Temos 3 arquivos no Google Drive:
#
#   1. EmendasParlamentares (planilha / CSV principal)
#      ID: 16LzXbx5fPph1u_QO-mbbxxBkgADDp-7_x_zXAlC-UkQ
#      Uso: ranking geral, perfil por parlamentar
#      Tamanho: ~3 MB
#
#   2. EmendasParlamentares_Convenios.csv
#      ID: 17D2GEU4W7Jh9c52UT2qm1RZN6FDlKaSA
#      Uso: tela de detalhe da emenda (convênios vinculados)
#      Tamanho: ~24 MB
#
#   3. EmendasParlamentares_PorFavorecido.csv
#      ID: 1qolBJ8BNZtRGT-68UMWTxGVM1lQY8uKu
#      Uso: busca por recebedor / favorecido
#      Tamanho: ~170 MB — carregado só quando necessário
#
# LÓGICA DE CADA FUNÇÃO:
#   1. Tenta baixar o CSV do Drive (dados completos)
#   2. Se falhar por qualquer motivo → cai na API (fallback)
#
# IMPORTANTE — PERMISSÃO DOS ARQUIVOS NO DRIVE:
#   Os arquivos precisam estar com acesso "Qualquer pessoa
#   com o link pode visualizar" para o download funcionar
#   sem autenticação no Streamlit Cloud.
#   No Drive: botão direito no arquivo → Compartilhar →
#   "Qualquer pessoa com o link" → Visualizador → Concluído
# ============================================================

import io
import requests
import pandas as pd
import streamlit as st

from utils.api_transparencia import (
    buscar_emendas_ranking,
    buscar_emendas_por_autor,
    buscar_emendas_por_municipio,
    buscar_emendas_por_favorecido,
)
from utils.api_camara import buscar_deputados_legislatura


# ============================================================
# IDs DOS ARQUIVOS NO GOOGLE DRIVE
# ============================================================

ID_EMENDAS_PRINCIPAL  = "1FWbRIT6a2i3d5Dz0rg6BCkO1My2XCTSw"   # 46 MB — CSV
ID_EMENDAS_CONVENIOS  = "17D2GEU4W7Jh9c52UT2qm1RZN6FDlKaSA"   # 24 MB — CSV
ID_EMENDAS_FAVORECIDO = "1qolBJ8BNZtRGT-68UMWTxGVM1lQY8uKu"   # 170 MB — CSV (Drive, fallback)

# URL direta via GitHub Releases — sem bloqueio de download
URL_FAVORECIDO_GITHUB = (
    "https://github.com/wcdatamarketing-sketch/emendas-parlamentares"
    "/releases/download/v1.0-data/EmendasParlamentares_PorFavorecido.csv"
)

# URL para arquivos até ~25 MB
URL_DOWNLOAD = "https://drive.google.com/uc?export=download&id={file_id}"

# URL para arquivos grandes (> 25 MB) — bypassa confirmação do Drive
# Usada para os 3 arquivos pois todos passam de 25 MB
URL_DOWNLOAD_GRANDE = (
    "https://drive.google.com/uc?export=download&confirm=t&id={file_id}"
)


# ============================================================
# MAPEAMENTO DE COLUNAS
# Traduz nomes do CSV (português) para camelCase (padrão da API)
# ============================================================

COLUNAS_PRINCIPAL = {
    "Código da Emenda":                   "codigoEmenda",
    "Ano da Emenda":                      "ano",
    "Tipo de Emenda":                     "tipoEmenda",
    "Código do Autor da Emenda":          "codigoAutor",
    "Nome do Autor da Emenda":            "nomeAutor",
    "Número da emenda":                   "numeroEmenda",
    "Localidade de aplicação do recurso": "localidadeDoGasto",
    "Código Município IBGE":              "codigoMunicipio",
    "Município":                          "municipioFavorecido",
    "Código UF IBGE":                     "codigoUF",
    "UF":                                 "ufFavorecido",
    "Região":                             "regiao",
    "Código Função":                      "codigoFuncao",
    "Nome Função":                        "funcao",
    "Código Subfunção":                   "codigoSubfuncao",
    "Nome Subfunção":                     "subfuncao",
    "Código Programa":                    "codigoPrograma",
    "Nome Programa":                      "nomePrograma",
    "Código Ação":                        "codigoAcao",
    "Nome Ação":                          "nomeAcao",
    "Código Plano Orçamentário":          "codigoPlanoOrcamentario",
    "Nome Plano Orçamentário":            "nomePlanoOrcamentario",
    "Valor Empenhado":                    "valorEmpenhado",
    "Valor Liquidado":                    "valorLiquidado",
    "Valor Pago":                         "valorPago",
    "Valor Restos A Pagar Inscritos":     "valorRestoInscrito",
    "Valor Restos A Pagar Cancelados":    "valorRestoCancelado",
    "Valor Restos A Pagar Pagos":         "valorRestoPago",
}

COLUNAS_CONVENIOS = {
    "Código da Emenda":         "codigoEmenda",
    "Código Função":            "codigoFuncao",
    "Nome Função":              "funcao",
    "Código Subfunção":         "codigoSubfuncao",
    "Nome Subfunção":           "subfuncao",
    "Localidade do gasto":      "localidadeDoGasto",
    "Tipo de Emenda":           "tipoEmenda",
    "Data Publicação Convênio": "dataPublicacaoConvenio",
    "Convenente":               "nomeFavorecido",
    "Objeto Convênio":          "objetoConvenio",
    "Número Convênio":          "numeroConvenio",
    "Valor Convênio":           "valorConvenio",
}

COLUNAS_FAVORECIDO = {
    # Colunas reais confirmadas no CSV (diagnóstico 12/05/2026)
    "Código da Emenda":       "codigoEmenda",
    "Código do Autor da Emenda": "codigoAutor",
    "Nome do Autor da Emenda": "nomeAutor",
    "Número da emenda":       "numeroEmenda",
    "Tipo de Emenda":         "tipoEmenda",
    "Ano/Mês":                "ano",
    "Código do Favorecido":   "codigoFavorecido",
    "Favorecido":             "nomeFavorecido",
    "Natureza Jurídica":      "naturezaJuridica",
    "Tipo Favorecido":        "tipoFavorecido",
    "UF Favorecido":          "ufFavorecido",
    "Município Favorecido":   "municipioFavorecido",
    "Valor Recebido":         "valorEmpenhado",
}

COLUNAS_VALOR = [
    "valorEmpenhado", "valorLiquidado", "valorPago",
    "valorRestoInscrito", "valorRestoCancelado", "valorRestoPago",
    "valorConvenio",
]


# ============================================================
# FUNÇÕES INTERNAS
# ============================================================

def _limpar_valor(valor_str) -> float:
    """Converte "1.500.000,50" → 1500000.50"""
    if valor_str is None or str(valor_str).strip() in ("", "—", "-", "S/I"):
        return 0.0
    try:
        s = str(valor_str).strip().replace(".", "").replace(",", ".")
        return float(s)
    except (ValueError, AttributeError):
        return 0.0


def _baixar_csv_drive(file_id: str, grande: bool = False) -> pd.DataFrame | None:
    """
    Baixa um CSV do Google Drive e retorna como DataFrame.
    Retorna None se o arquivo não estiver acessível.
    """
    url = (URL_DOWNLOAD_GRANDE if grande else URL_DOWNLOAD).format(file_id=file_id)

    try:
        resposta = requests.get(url, timeout=120)
        resposta.raise_for_status()

        # Tenta as combinações de separador e encoding mais comuns.
        # O Portal da Transparência exporta em latin-1 com ponto-e-vírgula.
        df = None
        for sep in [";", ","]:
            for enc in ["latin-1", "cp1252", "utf-8-sig", "utf-8"]:
                try:
                    df = pd.read_csv(
                        io.BytesIO(resposta.content),
                        sep=sep,
                        encoding=enc,
                        dtype=str,
                        low_memory=False,
                    )
                    # Só aceita se tiver mais de 1 coluna (leitura válida)
                    if len(df.columns) > 1:
                        break
                    df = None
                except Exception:
                    df = None
            if df is not None:
                break

        if df is None:
            raise ValueError("Não foi possível ler o CSV — encoding/separador desconhecido.")

        df.columns = df.columns.str.strip()
        return df

    except Exception as e:
        st.warning(f"⚠️ Não foi possível baixar dados do Drive ({e}). Usando API.")
        return None


def _aplicar_mapeamento(df: pd.DataFrame, mapeamento: dict) -> pd.DataFrame:
    """Renomeia colunas e converte valores monetários."""
    cols = {k: v for k, v in mapeamento.items() if k in df.columns}
    df = df.rename(columns=cols)
    for col in COLUNAS_VALOR:
        if col in df.columns:
            df[col] = df[col].apply(_limpar_valor)
    return df


def _df_para_lista(df: pd.DataFrame) -> list:
    """Converte DataFrame em lista de dicionários (formato da API)."""
    return df.fillna("").to_dict(orient="records")


# ============================================================
# CACHE DOS DATAFRAMES
# CSV histórico: TTL de 7 dias (dados não mudam)
# Complemento API 2026: TTL de 1h (dados recentes)
# ============================================================

@st.cache_data(ttl=86400, show_spinner="Carregando lista de deputados...")
def _nomes_deputados_federais() -> set:
    """
    Retorna um set com os nomes dos deputados federais da 57ª legislatura.
    Usado para filtrar senadores e outros da base CSV.
    TTL de 24h — lista muda raramente.
    """
    try:
        deputados = buscar_deputados_legislatura(57)
        # Normaliza os nomes para comparação: maiúsculas, sem espaços extras
        return set(d.get("nome", "").strip().upper() for d in deputados if d.get("nome"))
    except Exception:
        return set()  # Se falhar, não filtra (evita perder dados)


@st.cache_data(ttl=604800, show_spinner="Carregando base de emendas...")  # 7 dias — dados históricos
def _df_principal() -> pd.DataFrame | None:
    df = _baixar_csv_drive(ID_EMENDAS_PRINCIPAL, grande=True)  # 46 MB
    if df is not None:
        df = _aplicar_mapeamento(df, COLUNAS_PRINCIPAL)

        # Filtra senadores — mantém só deputados federais da 57ª legislatura
        # e registros sem autor identificado (anos antigos com "Sem informação")
        nomes_deputados = _nomes_deputados_federais()
        if nomes_deputados and "nomeAutor" in df.columns:
            sem_info = df["nomeAutor"].str.strip().str.upper().isin(
                {"SEM INFORMAÇÃO", "SEM INFORMACAO", "S/I", ""}
            )
            e_deputado = df["nomeAutor"].str.strip().str.upper().isin(nomes_deputados)
            df = df[sem_info | e_deputado].copy()

    return df


@st.cache_data(ttl=604800, show_spinner="Carregando base de convênios...")  # 7 dias
def _df_convenios() -> pd.DataFrame | None:
    df = _baixar_csv_drive(ID_EMENDAS_CONVENIOS, grande=False)
    if df is not None:
        df = _aplicar_mapeamento(df, COLUNAS_CONVENIOS)
    return df


@st.cache_data(ttl=604800, show_spinner="Carregando base de favorecidos...")  # 7 dias
def _df_favorecido() -> pd.DataFrame | None:
    """
    Baixa o CSV de favorecidos do GitHub Releases.
    Mostra status detalhado para diagnóstico.
    """
    try:
        resp = requests.get(URL_FAVORECIDO_GITHUB, timeout=180, allow_redirects=True)

        if resp.status_code != 200:
            return None

        df = None
        for sep in [";", ","]:
            for enc in ["latin-1", "cp1252", "utf-8-sig", "utf-8"]:
                try:
                    df = pd.read_csv(
                        io.BytesIO(resp.content),
                        sep=sep,
                        encoding=enc,
                        dtype=str,
                        low_memory=False,
                    )
                    if len(df.columns) > 3:
                        break
                    df = None
                except Exception as ex:
                    df = None
            if df is not None:
                break

        if df is None:
            return None

        df.columns = df.columns.str.strip()
        df = _aplicar_mapeamento(df, COLUNAS_FAVORECIDO)
        return df

    except Exception as e:
        st.warning(f"⚠️ Erro ao baixar favorecidos: {e}")
        return None


# ============================================================
# FUNÇÕES PÚBLICAS
# São essas que o cache.py vai chamar no lugar da API direta
# ============================================================

# Ano atual — usado para decidir se complementa com API
import datetime
ANO_ATUAL = datetime.date.today().year


@st.cache_data(ttl=3600)  # 1h — verifica dados recentes frequentemente
def _ultimo_mes_csv(ano: int) -> int | None:
    """
    Retorna o último mês disponível no CSV para um ano.
    Usado para saber a partir de quando complementar com a API.
    Retorna None se o ano não estiver no CSV.
    """
    df = _df_principal()
    if df is None or "ano" not in df.columns:
        return None
    df_ano = df[df["ano"].astype(str) == str(ano)]
    if df_ano.empty:
        return None
    # Se tiver coluna de mês/data, extrai o último mês
    for col in ["mesAno", "mes", "dataEmenda", "Ano/Mês"]:
        if col in df_ano.columns:
            try:
                meses = df_ano[col].astype(str).str[:7]  # "2026/03" ou "2026-03"
                ultimo = meses.dropna().max()
                return int(ultimo[-2:])  # pega o mês
            except Exception:
                pass
    # Se não tem coluna de mês, assume que o CSV tem o ano completo
    # (exceto para o ano atual — assume até mês anterior)
    if ano < ANO_ATUAL:
        return 12
    return datetime.date.today().month - 1 or 1


def carregar_emendas_ranking(api_key: str, ano: int) -> list:
    """
    Ranking geral — CSV para dados históricos, API para complementar 2026.

    Para anos anteriores ao atual: usa apenas o CSV (dados completos).
    Para o ano atual: usa CSV + complementa com API para meses faltantes.
    """
    df = _df_principal()
    resultados = []

    if df is not None and "ano" in df.columns:
        df_ano = df[df["ano"].astype(str) == str(ano)].copy()
        if not df_ano.empty:
            resultados = _df_para_lista(df_ano)

    # Para o ano atual, complementa com API se o CSV não tiver dados recentes
    if ano == ANO_ATUAL:
        try:
            dados_api = buscar_emendas_ranking(api_key, ano)
            if dados_api:
                # Junta CSV + API, remove duplicatas pelo codigoEmenda
                df_csv = pd.DataFrame(resultados) if resultados else pd.DataFrame()
                df_api = pd.DataFrame(dados_api)
                if not df_csv.empty and "codigoEmenda" in df_csv.columns and "codigoEmenda" in df_api.columns:
                    codigos_csv = set(df_csv["codigoEmenda"].dropna().unique())
                    df_novos = df_api[~df_api["codigoEmenda"].isin(codigos_csv)]
                    df_final = pd.concat([df_csv, df_novos], ignore_index=True)
                    return _df_para_lista(df_final)
                elif df_csv.empty:
                    return dados_api
        except Exception:
            pass  # Se API falhar, usa só o CSV

    if resultados:
        return resultados

    # Fallback total: API
    return buscar_emendas_ranking(api_key, ano)


def carregar_emendas_por_autor(api_key: str, nome_autor: str, ano: int) -> list:
    """Perfil do parlamentar — filtra o CSV principal por nome."""
    df = _df_principal()
    if df is not None and "nomeAutor" in df.columns:
        mask = df["nomeAutor"].str.contains(nome_autor, case=False, na=False)
        if "ano" in df.columns:
            mask = mask & (df["ano"].astype(str) == str(ano))
        df_filtrado = df[mask].copy()
        if not df_filtrado.empty:
            return _df_para_lista(df_filtrado)
    return buscar_emendas_por_autor(api_key, nome_autor, ano)


def carregar_emendas_por_municipio(api_key: str, municipio: str, ano: int) -> list:
    """Busca por município — filtra o CSV principal."""
    df = _df_principal()
    if df is not None and "municipioFavorecido" in df.columns:
        mask = df["municipioFavorecido"].str.contains(municipio, case=False, na=False)
        if "ano" in df.columns:
            mask = mask & (df["ano"].astype(str) == str(ano))
        df_filtrado = df[mask].copy()
        if not df_filtrado.empty:
            return _df_para_lista(df_filtrado)
    return buscar_emendas_por_municipio(api_key, municipio, ano)


def carregar_emendas_por_favorecido(api_key: str, nome_favorecido: str, ano: int) -> list:
    """Busca por favorecido — usa o CSV específico de 170 MB."""
    df = _df_favorecido()
    if df is not None and "nomeFavorecido" in df.columns:
        mask = df["nomeFavorecido"].str.contains(nome_favorecido, case=False, na=False)
        if "ano" in df.columns:
            mask = mask & (df["ano"].astype(str) == str(ano))
        df_filtrado = df[mask].copy()
        if not df_filtrado.empty:
            return _df_para_lista(df_filtrado)
    return buscar_emendas_por_favorecido(api_key, nome_favorecido, ano)


def carregar_top_favorecidos(
    nome_autor: str = None,
    sigla_partido: str = None,
    anos: list = None,
    top_n: int = 10,
) -> list:
    """
    Retorna os top favorecidos por valor recebido.

    Estratégia de cruzamento via codigoAutor (chave confiável):
    1. Busca os codigoAutor do deputado/partido no CSV principal
    2. Filtra o CSV de favorecidos por esses códigos
    3. Agrega por favorecido e retorna top N

    Isso evita problemas de variação de nome (maiúsculas, acentos etc.)
    """
    df_fav = _df_favorecido()
    if df_fav is None or df_fav.empty:
        return []

    df_princ = _df_principal()
    if df_princ is None or df_princ.empty:
        return []

    # Detecta coluna de código do autor nos dois CSVs
    col_cod_fav = next(
        (c for c in ["codigoAutor", "Código do Autor da Emenda"] if c in df_fav.columns), None
    )
    col_cod_princ = next(
        (c for c in ["codigoAutor", "Código do Autor da Emenda"] if c in df_princ.columns), None
    )

    if not col_cod_fav or not col_cod_princ:
        return []

    # Filtra CSV principal pelo deputado ou partido e anos
    df_p = df_princ.copy()
    if anos:
        df_p = df_p[df_p["ano"].astype(str).isin([str(a) for a in anos])]

    if nome_autor:
        # Busca por nome no CSV principal para pegar o(s) código(s) do autor
        col_nome = next(
            (c for c in ["nomeAutor", "Nome do Autor da Emenda"] if c in df_p.columns), None
        )
        if col_nome:
            nome_upper = nome_autor.strip().upper()
            df_p = df_p[df_p[col_nome].str.upper().str.contains(nome_upper, na=False, regex=False)]

    elif sigla_partido:
        col_partido = next(
            (c for c in ["partidoAutor", "siglaPartido"] if c in df_p.columns), None
        )
        if col_partido:
            df_p = df_p[df_p[col_partido].str.upper() == sigla_partido.upper()]

    if df_p.empty:
        return []

    # Pega os códigos de autor únicos
    codigos_autor = set(df_p[col_cod_princ].dropna().astype(str).unique())

    # Filtra CSV de favorecidos pelos códigos de autor
    df_fav = df_fav[df_fav[col_cod_fav].astype(str).isin(codigos_autor)]

    # Filtro de ano no CSV de favorecidos
    col_ano_fav = next(
        (c for c in ["ano", "Ano/Mês"] if c in df_fav.columns), None
    )
    if anos and col_ano_fav:
        df_fav = df_fav[df_fav[col_ano_fav].astype(str).str[:4].isin([str(a) for a in anos])]

    # Detecta colunas de favorecido e valor
    col_fav_nome = next(
        (c for c in ["nomeFavorecido", "Favorecido"] if c in df_fav.columns), None
    )
    col_val = next(
        (c for c in ["valorEmpenhado", "Valor Recebido"] if c in df_fav.columns), None
    )

    if df_fav.empty or not col_fav_nome or not col_val:
        return []

    # Converte valor para número se necessário
    if not pd.api.types.is_numeric_dtype(df_fav[col_val]):
        df_fav[col_val] = (
            df_fav[col_val].astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        df_fav[col_val] = pd.to_numeric(df_fav[col_val], errors="coerce").fillna(0)

    # Remove entradas sem favorecido e sem valor
    df_fav = df_fav[~df_fav[col_fav_nome].astype(str).str.strip().isin(["", "Sem informação", "S/I"])]
    df_fav = df_fav[df_fav[col_val] > 0]

    if df_fav.empty:
        return []

    # Limpa nome do favorecido — remove código numérico do início se houver
    # Ex: "8,09E+12 FUNDO MUNICIPAL DE SAUDE" → "FUNDO MUNICIPAL DE SAUDE"
    def _limpar_favorecido(nome):
        s = str(nome).strip()
        # Remove padrão "123456789 NOME" — código no início
        partes = s.split(" ", 1)
        if len(partes) == 2 and partes[0].replace(".", "").isdigit():
            return partes[1].strip()
        return s

    # Extrai ano
    if col_ano_fav:
        df_fav["_ano"] = df_fav[col_ano_fav].astype(str).str[:4]
    else:
        df_fav["_ano"] = "?"

    df_fav["_fav_limpo"] = df_fav[col_fav_nome].apply(_limpar_favorecido)

    # Agrega por favorecido
    top = (
        df_fav.groupby("_fav_limpo")
        .agg(
            valor=(col_val, "sum"),
            periodo=("_ano", lambda s: ", ".join(sorted(set(s)))),
        )
        .reset_index()
        .sort_values("valor", ascending=False)
        .head(top_n)
    )

    return [
        {
            "favorecido": row["_fav_limpo"],
            "valor":      row["valor"],
            "periodo":    row["periodo"],
        }
        for _, row in top.iterrows()
    ]


def carregar_detalhe_emenda(api_key: str, codigo_emenda: str) -> dict:
    """
    Detalhe de uma emenda — cruza CSV principal + convênios.
    """
    df = _df_principal()
    resultado = {}

    if df is not None and "codigoEmenda" in df.columns:
        df_emenda = df[df["codigoEmenda"] == codigo_emenda]
        if not df_emenda.empty:
            resultado = df_emenda.iloc[0].fillna("").to_dict()

            # Enriquece com dados de convênio se disponível
            df_conv = _df_convenios()
            if df_conv is not None and "codigoEmenda" in df_conv.columns:
                df_conv_filtrado = df_conv[df_conv["codigoEmenda"] == codigo_emenda]
                if not df_conv_filtrado.empty:
                    conv = df_conv_filtrado.iloc[0].fillna("").to_dict()
                    resultado["numeroConvenio"]          = conv.get("numeroConvenio", "")
                    resultado["nomeFavorecido"]           = conv.get("nomeFavorecido", "")
                    resultado["objetoConvenio"]           = conv.get("objetoConvenio", "")
                    resultado["dataPublicacaoConvenio"]   = conv.get("dataPublicacaoConvenio", "")
            return resultado

    from utils.api_transparencia import buscar_detalhe_emenda
    return buscar_detalhe_emenda(api_key, codigo_emenda)
