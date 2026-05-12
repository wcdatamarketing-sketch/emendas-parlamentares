# ============================================================
# pages/1_Ranking.py
# Tela inicial — ranking geral de parlamentares por emendas
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.cache import cache_emendas_ranking
from utils.formatters import (
    formatar_moeda,
    formatar_moeda_resumida,
    limpar_nome,
)


st.set_page_config(
    page_title="Ranking — Emendas Parlamentares",
    page_icon="📊",
    layout="wide",
)


# Verificação da chave de API
if "api_key" not in st.session_state:
    if "api_key" in st.secrets:
        st.session_state.api_key = st.secrets["api_key"]
    else:
        st.error("⚠️ Chave da API não configurada.")
        st.stop()

api_key = st.session_state.api_key


# ============================================================
# CABEÇALHO
# ============================================================

st.markdown(
    "<h1 style='color:#1a3a5c;'>📊 Ranking de Parlamentares</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "Parlamentares e bancadas ordenados pelo total de emendas. "
    "Use os filtros para refinar a busca."
)
st.divider()


# ============================================================
# FILTROS
# ============================================================

col_ano, col_tipo, col_local = st.columns(3)

with col_ano:
    ano = st.selectbox(
        "Ano",
        options=[2024, 2023, 2022],
        index=0,
    )

with col_tipo:
    tipo_emenda = st.selectbox(
        "Tipo de emenda",
        options=["Todas", "Emenda Individual", "Emenda de Bancada", "Emenda de Comissão", "Emenda de Relator"],
    )

with col_local:
    localidade = st.text_input(
        "Localidade do gasto",
        placeholder="Ex: AMAPÁ, SÃO PAULO...",
    )


# ============================================================
# BUSCA DOS DADOS
# ============================================================

with st.spinner("Buscando dados da API do Portal da Transparência..."):
    try:
        emendas_raw = cache_emendas_ranking(api_key, ano)
    except Exception as e:
        st.error(f"Erro detalhado: {str(e)}")
        st.stop()

if not emendas_raw:
    st.warning("Nenhum dado encontrado.")
    st.stop()


# ============================================================
# PROCESSAMENTO DOS DADOS
# ============================================================

df = pd.DataFrame(emendas_raw)

# Mostra ao usuário quais colunas estão disponíveis (útil para debug)
# st.write("Colunas disponíveis:", df.columns.tolist())

# Converte valores monetários para número
# (a API retorna esses campos como string em alguns casos)
for coluna in df.columns:
    if "valor" in coluna.lower():
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0)


# ============================================================
# APLICAÇÃO DOS FILTROS
# ============================================================

if tipo_emenda != "Todas" and "tipoEmenda" in df.columns:
    df = df[df["tipoEmenda"].str.contains(tipo_emenda, case=False, na=False)]

if localidade and "localidadeDoGasto" in df.columns:
    df = df[df["localidadeDoGasto"].str.contains(localidade, case=False, na=False)]

if df.empty:
    st.warning("Nenhum resultado com os filtros aplicados.")
    st.stop()


# ============================================================
# AGRUPAMENTO POR AUTOR
# ============================================================

# Identifica qual coluna de valor usar (pode variar por endpoint)
coluna_valor = None
for opcao in ["valor", "valorEmpenhado", "valorPago", "valorTotal"]:
    if opcao in df.columns:
        coluna_valor = opcao
        break

if not coluna_valor:
    st.error("API não retornou nenhum campo de valor. Colunas disponíveis: " + ", ".join(df.columns))
    st.stop()

# Agrupa por nome do autor da emenda
ranking = df.groupby("nomeAutor").agg(
    total=(coluna_valor, "sum"),
    quantidade=(coluna_valor, "count"),
    tipo=("tipoEmenda", "first"),
).reset_index()

ranking = ranking.sort_values("total", ascending=False)
ranking.insert(0, "posicao", range(1, len(ranking) + 1))


# ============================================================
# CARDS DE RESUMO
# ============================================================

st.markdown("### 📈 Resumo do ano")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Total de autores", len(ranking))

with c2:
    st.metric(
        "Total de emendas",
        f"{ranking['quantidade'].sum():,}".replace(",", "."),
    )

with c3:
    st.metric(
        "Valor total",
        formatar_moeda_resumida(ranking["total"].sum()),
    )

st.divider()


# ============================================================
# GRÁFICO TOP 20
# ============================================================

st.markdown("### 🏆 Top 20 por valor total")

top20 = ranking.head(20)

fig = px.bar(
    top20,
    x="total",
    y="nomeAutor",
    orientation="h",
    color="tipo",
    hover_data=["quantidade"],
    labels={
        "total": "Valor Total (R$)",
        "nomeAutor": "Autor",
        "tipo": "Tipo de Emenda",
    },
)

fig.update_layout(
    yaxis={"categoryorder": "total ascending"},
    height=600,
    showlegend=True,
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=200),
)

st.plotly_chart(fig, use_container_width=True)

st.divider()


# ============================================================
# TABELA COMPLETA
# ============================================================

st.markdown("### 📋 Ranking completo")

tabela = pd.DataFrame({
    "Pos.": ranking["posicao"],
    "Autor": ranking["nomeAutor"].apply(limpar_nome),
    "Tipo": ranking["tipo"],
    "Emendas": ranking["quantidade"],
    "Valor Total": ranking["total"].apply(formatar_moeda),
})

st.dataframe(
    tabela,
    use_container_width=True,
    hide_index=True,
    height=500,
)

# Botão de download
csv = ranking.to_csv(index=False, encoding="utf-8-sig")

st.download_button(
    label="⬇️ Baixar dados em CSV",
    data=csv,
    file_name=f"ranking_emendas_{ano}.csv",
    mime="text/csv",
)
