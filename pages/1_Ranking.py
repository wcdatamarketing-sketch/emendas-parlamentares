# ============================================================
# pages/1_Ranking.py
# Tela inicial — ranking geral de parlamentares por emendas
# Permite selecionar múltiplos anos para análise combinada
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.cache import cache_emendas_ranking
from utils.formatters import (
    formatar_moeda,
    formatar_moeda_resumida,
    calcular_percentual_execucao,
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
    "Selecione um ou mais anos para análise combinada."
)
st.divider()


# ============================================================
# FILTROS
# ============================================================

# Anos disponíveis na legislatura atual (2023-2026)
ANOS_DISPONIVEIS = [2026, 2025, 2024, 2023]

col_ano, col_tipo, col_local = st.columns([2, 2, 2])

with col_ano:
    # multiselect permite escolher múltiplas opções
    # default define quais já vêm marcados ao carregar a página
    anos_selecionados = st.multiselect(
        "Anos (selecione um ou mais)",
        options=ANOS_DISPONIVEIS,
        default=ANOS_DISPONIVEIS,  # todos marcados por padrão
        help="Selecione um ou mais anos para análise combinada"
    )

with col_tipo:
    tipo_emenda = st.selectbox(
        "Tipo de emenda",
        options=["Todas", "Individual", "Bancada", "Comissão", "Relator"],
    )

with col_local:
    localidade = st.text_input(
        "Localidade do gasto",
        placeholder="Ex: AMAPÁ, SÃO PAULO...",
    )

# Valida se pelo menos um ano foi selecionado
if not anos_selecionados:
    st.warning("⚠️ Selecione pelo menos um ano para visualizar o ranking.")
    st.stop()


# ============================================================
# BUSCA DOS DADOS (múltiplos anos)
# ============================================================

# Ordena os anos selecionados em ordem crescente para a busca
anos_ordenados = sorted(anos_selecionados)

# Lista que vai acumular as emendas de todos os anos selecionados
todas_emendas = []

# Spinner com mensagem que será atualizada para cada ano
with st.spinner(f"Buscando dados de {len(anos_ordenados)} ano(s)..."):

    # Loop em cada ano selecionado
    for ano_atual in anos_ordenados:
        try:
            # Busca os dados do ano específico
            emendas_do_ano = cache_emendas_ranking(api_key, ano_atual)

            # Adiciona o campo "ano" em cada registro para sabermos a origem
            # (a API já retorna o campo "ano", mas garantimos aqui também)
            for emenda in emendas_do_ano:
                emenda["ano"] = ano_atual

            # Junta com a lista geral
            todas_emendas.extend(emendas_do_ano)

        except Exception as e:
            st.error(f"Erro ao buscar dados de {ano_atual}: {str(e)}")
            st.stop()

# Se nenhuma emenda retornou em nenhum ano
if not todas_emendas:
    st.warning("Nenhum dado encontrado nos anos selecionados.")
    st.stop()


# ============================================================
# PROCESSAMENTO DOS DADOS
# ============================================================

df = pd.DataFrame(todas_emendas)

# Converte os valores monetários (formato brasileiro → número)
colunas_valor = [
    "valorEmpenhado", "valorLiquidado", "valorPago",
    "valorRestoInscrito", "valorRestoCancelado", "valorRestoPago"
]

for coluna in colunas_valor:
    if coluna in df.columns:
        df[coluna] = (
            df[coluna]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
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

# Função auxiliar para juntar os anos únicos em uma string
# Exemplo: para os anos [2023, 2024, 2025] → "2023, 2024, 2025"
def juntar_anos(series):
    """
    Recebe uma coluna do pandas com anos e retorna string
    com os anos únicos ordenados.
    """
    # set() pega só valores únicos, sorted() ordena
    anos_unicos = sorted(set(series))
    # join junta os valores numa string separados por vírgula
    return ", ".join(str(a) for a in anos_unicos)


# Agrupa por autor e calcula totais consolidados de todos os anos
ranking = df.groupby("nomeAutor").agg(
    total_empenhado=("valorEmpenhado", "sum"),
    total_pago=("valorPago", "sum"),
    quantidade=("valorEmpenhado", "count"),
    tipo=("tipoEmenda", "first"),
    periodo=("ano", juntar_anos),  # nova coluna com os anos
).reset_index()

ranking = ranking.sort_values("total_empenhado", ascending=False)

# Calcula percentual de execução
ranking["execucao"] = ranking.apply(
    lambda row: calcular_percentual_execucao(
        row["total_empenhado"], row["total_pago"]
    ),
    axis=1,
)

ranking.insert(0, "posicao", range(1, len(ranking) + 1))


# ============================================================
# CARDS DE RESUMO
# ============================================================

# Card adicional mostrando o período selecionado
periodo_label = ", ".join(str(a) for a in sorted(anos_selecionados))
st.markdown(
    f"### 📈 Resumo — Período: **{periodo_label}**"
)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Total de autores", len(ranking))

with c2:
    st.metric(
        "Total de emendas",
        f"{ranking['quantidade'].sum():,}".replace(",", "."),
    )

with c3:
    st.metric(
        "Empenhado",
        formatar_moeda_resumida(ranking["total_empenhado"].sum()),
    )

with c4:
    st.metric(
        "Pago",
        formatar_moeda_resumida(ranking["total_pago"].sum()),
    )

st.divider()


# ============================================================
# GRÁFICO TOP 20
# ============================================================

st.markdown("### 🏆 Top 20 por valor empenhado")

top20 = ranking.head(20)

fig = px.bar(
    top20,
    x="total_empenhado",
    y="nomeAutor",
    orientation="h",
    color="tipo",
    hover_data=["quantidade", "execucao", "periodo"],
    labels={
        "total_empenhado": "Empenhado (R$)",
        "nomeAutor": "Autor",
        "tipo": "Tipo de Emenda",
        "periodo": "Período",
    },
)

fig.update_layout(
    yaxis={"categoryorder": "total ascending"},
    height=600,
    showlegend=True,
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=250),
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
    "Período": ranking["periodo"],
    "Emendas": ranking["quantidade"],
    "Empenhado": ranking["total_empenhado"].apply(formatar_moeda),
    "Pago": ranking["total_pago"].apply(formatar_moeda),
    "Execução": ranking["execucao"],
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
    file_name=f"ranking_emendas_{'_'.join(str(a) for a in sorted(anos_selecionados))}.csv",
    mime="text/csv",
)


# ============================================================
# RODAPÉ — ADMINISTRAÇÃO
# ============================================================

st.divider()

# Botão discreto de limpar cache no rodapé (para administrador)
col_rod_esq, col_rod_btn, col_rod_dir = st.columns([3, 2, 3])

with col_rod_btn:
    if st.button("🔄 Atualizar dados (limpar cache)", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown(
    "<p style='text-align:center; color:#999; font-size:0.85rem; margin-top:1rem;'>"
    "Dados obtidos via API do Portal da Transparência — CGU. "
    "Atualização automática a cada hora."
    "</p>",
    unsafe_allow_html=True
)
