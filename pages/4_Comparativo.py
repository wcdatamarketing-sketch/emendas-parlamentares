# ============================================================
# pages/4_Comparativo.py
# Tela de comparação entre dois parlamentares —
# exibe os dados lado a lado sem julgamentos
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px

# Importamos as funções de cache necessárias
from utils.cache import cache_emendas_por_autor

# Importamos os formatadores
from utils.formatters import (
    formatar_moeda,
    formatar_moeda_resumida,
    calcular_percentual_execucao,
    limpar_nome,
)


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Comparativo — Emendas Parlamentares",
    page_icon="⚖️",
    layout="wide",
)


# ============================================================
# VERIFICAÇÃO DA CHAVE DE API
# ============================================================

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
    "<h1 style='color:#1a3a5c;'>⚖️ Comparativo entre Parlamentares</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "Selecione dois parlamentares para ver os dados lado a lado. "
    "Apenas dados públicos — sem julgamentos."
)
st.divider()


# ============================================================
# CAMPOS DE BUSCA DOS DOIS PARLAMENTARES
# ============================================================

# Divide a tela em três partes — parlamentar A, separador, parlamentar B
col_a, col_vs, col_b = st.columns([5, 1, 5])

with col_a:
    st.markdown("#### 🔵 Parlamentar A")
    nome_a = st.text_input(
        "Nome do primeiro parlamentar",
        placeholder="Digite o nome...",
        key="nome_a",
    )

with col_vs:
    # Espaço vertical para alinhar o "VS" com os campos
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown(
        "<h2 style='text-align:center; color:#999;'>VS</h2>",
        unsafe_allow_html=True
    )

with col_b:
    st.markdown("#### 🔴 Parlamentar B")
    nome_b = st.text_input(
        "Nome do segundo parlamentar",
        placeholder="Digite o nome...",
        key="nome_b",
    )

# Seletor de ano centralizado abaixo dos campos
col_espaco, col_ano, col_espaco2 = st.columns([3, 2, 3])
with col_ano:
    ano = st.selectbox(
        "Ano de referência",
        options=[2024, 2023, 2022],
    )

# Só executa se os dois nomes foram preenchidos
if not nome_a or not nome_b:
    st.info("👆 Preencha os nomes dos dois parlamentares para comparar.")
    st.stop()

# Impede comparar o parlamentar com ele mesmo
if nome_a.strip().lower() == nome_b.strip().lower():
    st.warning("Digite nomes diferentes para comparar dois parlamentares distintos.")
    st.stop()


# ============================================================
# BUSCA DOS DADOS DOS DOIS PARLAMENTARES
# ============================================================

# Busca os dois em paralelo exibindo um spinner único
with st.spinner("Buscando dados dos dois parlamentares..."):

    emendas_a = cache_emendas_por_autor(api_key, nome_a, ano)
    emendas_b = cache_emendas_por_autor(api_key, nome_b, ano)

# Verifica se encontrou dados para os dois
if not emendas_a:
    st.warning(f"Nenhuma emenda encontrada para '{nome_a}' em {ano}.")
    st.stop()

if not emendas_b:
    st.warning(f"Nenhuma emenda encontrada para '{nome_b}' em {ano}.")
    st.stop()

# Converte para DataFrame
df_a = pd.DataFrame(emendas_a)
df_b = pd.DataFrame(emendas_b)

# Garante que as colunas de valor são numéricas nos dois DataFrames
for df in [df_a, df_b]:
    for coluna in ["valorEmpenhado", "valorPago", "valorLiquidado"]:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0)

# Pega o nome real retornado pela API (pode ter acentos diferentes)
nome_real_a = limpar_nome(
    df_a["nomeAutor"].iloc[0] if "nomeAutor" in df_a.columns else nome_a
)
nome_real_b = limpar_nome(
    df_b["nomeAutor"].iloc[0] if "nomeAutor" in df_b.columns else nome_b
)

# Calcula os totais de cada parlamentar
total_emp_a = df_a["valorEmpenhado"].sum()
total_emp_b = df_b["valorEmpenhado"].sum()
total_pago_a = df_a["valorPago"].sum() if "valorPago" in df_a.columns else 0
total_pago_b = df_b["valorPago"].sum() if "valorPago" in df_b.columns else 0
qtd_a = len(df_a)
qtd_b = len(df_b)


# ============================================================
# CABEÇALHO COMPARATIVO
# ============================================================

st.divider()

# Exibe os nomes dos dois parlamentares lado a lado
col_nome_a, col_meio, col_nome_b = st.columns([5, 1, 5])

with col_nome_a:
    partido_a = df_a["partidoAutor"].iloc[0] if "partidoAutor" in df_a.columns else "—"
    uf_a = df_a["ufAutor"].iloc[0] if "ufAutor" in df_a.columns else "—"
    st.markdown(f"""
        <div style='background:#e8f0fa; padding:1rem; border-radius:8px;
                    border-left:5px solid #2e6da4;'>
            <h3 style='color:#1a3a5c; margin:0;'>{nome_real_a}</h3>
            <p style='color:#555; margin:0;'>{partido_a} — {uf_a}</p>
        </div>
    """, unsafe_allow_html=True)

with col_meio:
    st.markdown("<br>", unsafe_allow_html=True)

with col_nome_b:
    partido_b = df_b["partidoAutor"].iloc[0] if "partidoAutor" in df_b.columns else "—"
    uf_b = df_b["ufAutor"].iloc[0] if "ufAutor" in df_b.columns else "—"
    st.markdown(f"""
        <div style='background:#faeaea; padding:1rem; border-radius:8px;
                    border-left:5px solid #c0392b;'>
            <h3 style='color:#7b1a1a; margin:0;'>{nome_real_b}</h3>
            <p style='color:#555; margin:0;'>{partido_b} — {uf_b}</p>
        </div>
    """, unsafe_allow_html=True)


# ============================================================
# CARDS COMPARATIVOS
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 📊 Dados comparativos")

# Função auxiliar para criar um card colorido
# criamos essa função aqui dentro pois só é usada nessa tela
def card_metrica(titulo, valor_a, valor_b):
    """
    Exibe dois cards lado a lado com os valores de cada parlamentar.
    titulo:  rótulo da métrica
    valor_a: valor formatado do parlamentar A
    valor_b: valor formatado do parlamentar B
    """
    col1, col2, col3 = st.columns([5, 1, 5])
    with col1:
        st.metric(label=f"🔵 {titulo}", value=valor_a)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
    with col3:
        st.metric(label=f"🔴 {titulo}", value=valor_b)

# Exibe os cards comparativos
card_metrica(
    "Total de emendas",
    str(qtd_a),
    str(qtd_b),
)
card_metrica(
    "Total empenhado",
    formatar_moeda_resumida(total_emp_a),
    formatar_moeda_resumida(total_emp_b),
)
card_metrica(
    "Total pago",
    formatar_moeda_resumida(total_pago_a),
    formatar_moeda_resumida(total_pago_b),
)
card_metrica(
    "Taxa de execução",
    calcular_percentual_execucao(total_emp_a, total_pago_a),
    calcular_percentual_execucao(total_emp_b, total_pago_b),
)
card_metrica(
    "Estados beneficiados",
    str(df_a["ufFavorecido"].nunique()) if "ufFavorecido" in df_a.columns else "—",
    str(df_b["ufFavorecido"].nunique()) if "ufFavorecido" in df_b.columns else "—",
)

st.divider()


# ============================================================
# GRÁFICO COMPARATIVO — ÁREAS TEMÁTICAS
# ============================================================

st.markdown("### 🎯 Distribuição por área temática")

if "funcao" in df_a.columns and "funcao" in df_b.columns:

    col_graf_a, col_graf_b = st.columns(2)

    with col_graf_a:
        st.markdown(f"**🔵 {nome_real_a}**")

        area_a = df_a.groupby("funcao")["valorEmpenhado"].sum().reset_index()
        area_a.columns = ["Área", "Valor"]

        fig_a = px.pie(
            area_a,
            names="Área",
            values="Valor",
            hole=0.4,
            # paleta de azuis para o parlamentar A
            color_discrete_sequence=px.colors.sequential.Blues_r,
        )
        fig_a.update_layout(height=320, margin=dict(t=10, b=10))
        st.plotly_chart(fig_a, use_container_width=True)

    with col_graf_b:
        st.markdown(f"**🔴 {nome_real_b}**")

        area_b = df_b.groupby("funcao")["valorEmpenhado"].sum().reset_index()
        area_b.columns = ["Área", "Valor"]

        fig_b = px.pie(
            area_b,
            names="Área",
            values="Valor",
            hole=0.4,
            # paleta de vermelhos para o parlamentar B
            color_discrete_sequence=px.colors.sequential.Reds_r,
        )
        fig_b.update_layout(height=320, margin=dict(t=10, b=10))
        st.plotly_chart(fig_b, use_container_width=True)

st.divider()


# ============================================================
# GRÁFICO COMPARATIVO — ESTADOS BENEFICIADOS
# ============================================================

st.markdown("### 🗺️ Estados mais beneficiados")

if "ufFavorecido" in df_a.columns and "ufFavorecido" in df_b.columns:

    # Agrupa os dois DataFrames por UF
    uf_a = df_a.groupby("ufFavorecido")["valorEmpenhado"].sum().reset_index()
    uf_a.columns = ["UF", "Valor"]
    uf_a["Parlamentar"] = nome_real_a

    uf_b = df_b.groupby("ufFavorecido")["valorEmpenhado"].sum().reset_index()
    uf_b.columns = ["UF", "Valor"]
    uf_b["Parlamentar"] = nome_real_b

    # pd.concat junta os dois DataFrames em um só
    # ignore_index=True reinicia o índice do DataFrame resultante
    uf_combinado = pd.concat([uf_a, uf_b], ignore_index=True)

    # Gráfico de barras agrupadas — um grupo por UF, uma barra por parlamentar
    fig_uf = px.bar(
        uf_combinado,
        x="UF",
        y="Valor",
        color="Parlamentar",    # uma cor por parlamentar
        barmode="group",        # barras lado a lado (group) em vez de empilhadas (stack)
        color_discrete_map={
            nome_real_a: "#2e6da4",   # azul para o parlamentar A
            nome_real_b: "#c0392b",   # vermelho para o parlamentar B
        },
        labels={
            "Valor": "Total Empenhado (R$)",
            "UF": "Estado",
        },
    )
    fig_uf.update_layout(
        height=400,
        plot_bgcolor="white",
        margin=dict(t=20, b=20),
    )
    st.plotly_chart(fig_uf, use_container_width=True)

st.divider()


# ============================================================
# TABELAS LADO A LADO
# ============================================================

st.markdown("### 📋 Lista de emendas")

col_tab_a, col_tab_b = st.columns(2)

def montar_tabela(df, nome):
    """
    Monta uma tabela resumida das emendas de um parlamentar.
    Reutilizamos essa função para os dois parlamentares
    em vez de repetir o mesmo código duas vezes.
    """
    colunas = {
        "tipoEmenda": "Tipo",
        "funcao": "Área",
        "municipioFavorecido": "Município",
        "ufFavorecido": "UF",
        "valorEmpenhado": "Empenhado",
        "valorPago": "Pago",
    }
    # Filtra apenas colunas existentes
    cols = {k: v for k, v in colunas.items() if k in df.columns}
    tabela = df[list(cols.keys())].copy()
    tabela.columns = list(cols.values())

    if "Empenhado" in tabela.columns:
        tabela["Empenhado"] = tabela["Empenhado"].apply(formatar_moeda)
    if "Pago" in tabela.columns:
        tabela["Pago"] = tabela["Pago"].apply(formatar_moeda)

    return tabela

with col_tab_a:
    st.markdown(f"**🔵 {nome_real_a}**")
    st.dataframe(
        montar_tabela(df_a, nome_real_a),
        use_container_width=True,
        hide_index=True,
        height=350,
    )

with col_tab_b:
    st.markdown(f"**🔴 {nome_real_b}**")
    st.dataframe(
        montar_tabela(df_b, nome_real_b),
        use_container_width=True,
        hide_index=True,
        height=350,
    )
