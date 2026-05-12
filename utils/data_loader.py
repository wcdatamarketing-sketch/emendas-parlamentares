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
# Cada arquivo é baixado UMA vez e mantido em memória por 1h
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


@st.cache_data(ttl=3600, show_spinner="Carregando base de emendas...")
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


@st.cache_data(ttl=3600, show_spinner="Carregando base de convênios...")
def _df_convenios() -> pd.DataFrame | None:
    df = _baixar_csv_drive(ID_EMENDAS_CONVENIOS, grande=False)
    if df is not None:
        df = _aplicar_mapeamento(df, COLUNAS_CONVENIOS)
    return df


@st.cache_data(ttl=3600, show_spinner="Carregando base de favorecidos...")
def _df_favorecido() -> pd.DataFrame | None:
    """
    Baixa o CSV de favorecidos do GitHub Releases.
    Mostra status detalhado para diagnóstico.
    """
    try:
        st.info(f"📥 Baixando CSV de favorecidos do GitHub...")
        resp = requests.get(URL_FAVORECIDO_GITHUB, timeout=180, allow_redirects=True)
        st.info(f"📊 Status HTTP: {resp.status_code} | Tamanho: {len(resp.content):,} bytes")

        if resp.status_code != 200:
            st.error(f"❌ Erro HTTP {resp.status_code}: {resp.content[:200]}")
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
                        st.info(f"✅ CSV lido: {len(df)} linhas | {len(df.columns)} colunas | sep='{sep}' enc='{enc}'")
                        st.info(f"📋 Colunas: {list(df.columns)[:5]}...")
                        break
                    df = None
                except Exception as ex:
                    df = None
            if df is not None:
                break

        if df is None:
            st.error("❌ Não foi possível ler o CSV com nenhuma combinação.")
            return None

        df.columns = df.columns.str.strip()
        df = _aplicar_mapeamento(df, COLUNAS_FAVORECIDO)
        return df

    except Exception as e:
        st.error(f"❌ Erro ao baixar favorecidos: {e}")
        return None


# ============================================================
# FUNÇÕES PÚBLICAS
# São essas que o cache.py vai chamar no lugar da API direta
# ============================================================

def carregar_emendas_ranking(api_key: str, ano: int) -> list:
    """Ranking geral — usa CSV principal (dados completos)."""
    df = _df_principal()
    if df is not None:
        df_ano = df[df["ano"].astype(str) == str(ano)].copy() if "ano" in df.columns else df.copy()
        if not df_ano.empty:
            return _df_para_lista(df_ano)
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
    Retorna os top favorecidos (recebedores reais) por valor empenhado.
    Usa o CSV de favorecidos (170 MB) que tem nomeFavorecido.

    Filtra por nome do autor (deputado) OU por partido.
    Retorna lista de dicts: [{"favorecido": str, "valor": float, "periodo": str}]
    """
    df = _df_favorecido()
    if df is None or df.empty:
        return []

    # Filtro por anos
    if anos and "ano" in df.columns:
        df = df[df["ano"].astype(str).isin([str(a) for a in anos])]

    # Filtro por autor — o CSV tem nomes em MAIÚSCULAS
    # Usa str.contains case-insensitive para tolerar variações de formatação
    if nome_autor and "nomeAutor" in df.columns:
        # Mostra amostra dos nomes no CSV para diagnóstico
        amostra = df["nomeAutor"].dropna().unique()[:5].tolist()
        st.info(f"🔍 Buscando '{nome_autor}' | Exemplos no CSV: {amostra}")
        nome_upper = nome_autor.strip().upper()
        df_filtrado = df[df["nomeAutor"].str.upper().str.contains(nome_upper, na=False, regex=False)]
        st.info(f"📊 Linhas encontradas para '{nome_autor}': {len(df_filtrado)}")
        st.info(f"📋 Colunas após filtro: {list(df_filtrado.columns)}")
        if "nomeFavorecido" in df_filtrado.columns:
            amostra_fav = df_filtrado["nomeFavorecido"].dropna().unique()[:3].tolist()
            st.info(f"🏢 Exemplos de favorecidos: {amostra_fav}")
        else:
            st.error(f"❌ Coluna nomeFavorecido NÃO encontrada! Colunas: {list(df_filtrado.columns)}")
        df = df_filtrado

    elif sigla_partido:
        # CSV de favorecidos não tem coluna de partido.
        # Cruzamos com o CSV principal para pegar os códigos de emenda do partido,
        # depois filtramos o CSV de favorecidos por esses códigos.
        df_principal = _df_principal()
        if df_principal is None or "codigoEmenda" not in df_principal.columns:
            return []

        col_partido_princ = next(
            (c for c in ["partidoAutor", "siglaPartido"] if c in df_principal.columns),
            None,
        )
        if not col_partido_princ:
            return []

        # Filtra CSV principal pelo partido e anos para pegar os códigos
        df_p = df_principal.copy()
        if anos:
            df_p = df_p[df_p["ano"].astype(str).isin([str(a) for a in anos])]
        df_p = df_p[df_p[col_partido_princ].str.upper() == sigla_partido.upper()]

        if df_p.empty:
            return []

        codigos = set(df_p["codigoEmenda"].dropna().unique())

        if "codigoEmenda" not in df.columns:
            return []

        df = df[df["codigoEmenda"].isin(codigos)]

    if df.empty or "nomeFavorecido" not in df.columns:
        return []

    # Remove entradas sem favorecido identificado
    df = df[~df["nomeFavorecido"].str.strip().isin(["", "Sem informação", "S/I", "SEM INFORMACAO"])]
    df = df[df["valorEmpenhado"] > 0]

    if df.empty:
        return []

    # Agrega por favorecido
    top = (
        df.groupby("nomeFavorecido")
        .agg(
            valor=("valorEmpenhado", "sum"),
            periodo=("ano", lambda s: ", ".join(sorted(set(s.astype(str))))),
        )
        .reset_index()
        .sort_values("valor", ascending=False)
        .head(top_n)
    )

    return [
        {
            "favorecido": row["nomeFavorecido"],
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
