# ============================================================
# pages/1_Ranking.py
# Ranking geral de parlamentares por emendas
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

if "api_key" not in st.session_state:
    if "api_key" in st.secrets:
        st.session_state.api_key = st.secrets["api_key"]
    else:
        st.error("⚠️ Chave da API não configurada.")
        st.stop()

api_key = st.session_state.api_key


# ============================================================
# ABREVIAÇÃO DO TIPO DE EMENDA
# ============================================================

TIPO_RESUMIDO = {
    "individual": "Individual",
    "bancada":    "Bancada",
    "comissão":   "Comissão",
    "comissao":   "Comissão",
    "relator":    "Relator",
}

def resumir_tipo(tipo_str) -> str:
    """
    Abrevia o tipo de emenda para exibição na tabela.
    "Emenda Individual - Transferências com Finalidade Definida"
    → "Individual"
    """
    if not tipo_str:
        return "—"
    s = str(tipo_str).lower()
    for chave, valor in TIPO_RESUMIDO.items():
        if chave in s:
            return valor
    return str(tipo_str).split("-")[0].strip().title()


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
# BUSCA DOS DADOS — carrega tudo primeiro para popular os filtros
# ============================================================

ANOS_DISPONIVEIS = [2023, 2024, 2025, 2026]
todas_emendas = []

with st.spinner("Carregando base de emendas..."):
    for ano_atual in ANOS_DISPONIVEIS:
        try:
            emendas_do_ano = cache_emendas_ranking(api_key, ano_atual)
            for emenda in emendas_do_ano:
                emenda["ano"] = ano_atual
            todas_emendas.extend(emendas_do_ano)
        except Exception as e:
            st.error(f"Erro ao buscar dados de {ano_atual}: {str(e)}")
            st.stop()

if not todas_emendas:
    st.warning("Nenhum dado encontrado.")
    st.stop()

df_base = pd.DataFrame(todas_emendas)

# Converte valores monetários — só converte se ainda não for numérico
# (o data_loader já pode ter feito isso; reconverter corromperia os valores)
colunas_valor_base = [
    "valorEmpenhado", "valorLiquidado", "valorPago",
    "valorRestoInscrito", "valorRestoCancelado", "valorRestoPago"
]
for coluna in colunas_valor_base:
    if coluna in df_base.columns:
        if not pd.api.types.is_numeric_dtype(df_base[coluna]):
            df_base[coluna] = (
                df_base[coluna].astype(str)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            df_base[coluna] = pd.to_numeric(df_base[coluna], errors="coerce").fillna(0)
        else:
            df_base[coluna] = df_base[coluna].fillna(0)

if "tipoEmenda" in df_base.columns:
    df_base["tipoResumido"] = df_base["tipoEmenda"].apply(resumir_tipo)

# Listas para os selects — extraídas da base real
lista_ufs = sorted([
    u for u in df_base["ufFavorecido"].dropna().unique()
    if str(u).strip() not in ("", "Sem informação", "S/I")
]) if "ufFavorecido" in df_base.columns else []

lista_autores = sorted([
    limpar_nome(a) for a in df_base["nomeAutor"].dropna().unique()
    if str(a).strip() not in ("", "Sem informação", "S/I")
]) if "nomeAutor" in df_base.columns else []


# ============================================================
# FILTROS
# ============================================================

# --- Linha 1: Anos como checkboxes ---
st.markdown("**Anos**")
col_2023, col_2024, col_2025, col_2026, col_espaco = st.columns([1, 1, 1, 1, 4])
with col_2023:
    ano_2023 = st.checkbox("2023", value=True)
with col_2024:
    ano_2024 = st.checkbox("2024", value=True)
with col_2025:
    ano_2025 = st.checkbox("2025", value=True)
with col_2026:
    ano_2026 = st.checkbox("2026", value=True)

anos_selecionados = [
    a for a, sel in [(2023, ano_2023), (2024, ano_2024), (2025, ano_2025), (2026, ano_2026)]
    if sel
]

if not anos_selecionados:
    st.warning("⚠️ Selecione pelo menos um ano.")
    st.stop()

# --- Linha 2: demais filtros ---
col_tipo, col_autor, col_uf, col_mun = st.columns([2, 3, 2, 3])

with col_tipo:
    tipo_emenda = st.selectbox(
        "Tipo de emenda",
        options=["Todas", "Individual", "Bancada", "Comissão", "Relator"],
    )

with col_autor:
    autor_sel = st.selectbox(
        "Autor",
        options=["Todos"] + lista_autores,
    )

with col_uf:
    uf_sel = st.selectbox(
        "UF",
        options=["Todas"] + lista_ufs,
    )

with col_mun:
    # Municípios filtrados pela UF selecionada
    if uf_sel != "Todas" and "ufFavorecido" in df_base.columns and "municipioFavorecido" in df_base.columns:
        lista_muns = sorted([
            m for m in df_base[df_base["ufFavorecido"] == uf_sel]["municipioFavorecido"].dropna().unique()
            if str(m).strip() not in ("", "Sem informação", "S/I")
        ])
    elif "municipioFavorecido" in df_base.columns:
        lista_muns = sorted([
            m for m in df_base["municipioFavorecido"].dropna().unique()
            if str(m).strip() not in ("", "Sem informação", "S/I")
        ])
    else:
        lista_muns = []

    mun_sel = st.selectbox(
        "Município",
        options=["Todos"] + lista_muns,
    )


# ============================================================
# PROCESSAMENTO
# ============================================================

# ============================================================
# APLICAÇÃO DOS FILTROS SOBRE df_base
# ============================================================

df = df_base.copy()

# Ano
df = df[df["ano"].astype(str).isin([str(a) for a in anos_selecionados])]

# Tipo de emenda
if tipo_emenda != "Todas" and "tipoResumido" in df.columns:
    df = df[df["tipoResumido"] == tipo_emenda]

# Autor
if autor_sel != "Todos" and "nomeAutor" in df.columns:
    df = df[df["nomeAutor"].apply(limpar_nome) == autor_sel]

# UF
if uf_sel != "Todas" and "ufFavorecido" in df.columns:
    df = df[df["ufFavorecido"] == uf_sel]

# Município
if mun_sel != "Todos" and "municipioFavorecido" in df.columns:
    df = df[df["municipioFavorecido"] == mun_sel]

if df.empty:
    st.warning("Nenhum resultado com os filtros aplicados.")
    st.stop()


# ============================================================
# AGRUPAMENTO POR AUTOR
# ============================================================

def juntar_anos(series):
    return ", ".join(str(a) for a in sorted(set(series)))

ranking = df.groupby("nomeAutor").agg(
    total_empenhado=("valorEmpenhado", "sum"),
    total_pago=("valorPago", "sum"),
    quantidade=("valorEmpenhado", "count"),
    tipo=("tipoResumido", "first"),
    periodo=("ano", juntar_anos),
).reset_index()

ranking = ranking.sort_values("total_empenhado", ascending=False)

ranking["execucao_pct"] = ranking.apply(
    lambda r: (r["total_pago"] / r["total_empenhado"] * 100)
    if r["total_empenhado"] > 0 else 0,
    axis=1,
).clip(upper=100)

ranking["execucao"] = ranking["execucao_pct"].apply(
    lambda v: f"{v:.1f}%".replace(".", ",")
)

ranking.insert(0, "posicao", range(1, len(ranking) + 1))


# ============================================================
# CARDS DE RESUMO — 5 métricas
# ============================================================

periodo_label = ", ".join(str(a) for a in sorted(anos_selecionados))
st.markdown(f"### 📈 Resumo — Período: **{periodo_label}**")

total_emp = ranking["total_empenhado"].sum()
total_pago = ranking["total_pago"].sum()
pct_geral = (total_pago / total_emp * 100) if total_emp > 0 else 0
pct_geral = min(pct_geral, 100.0)

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.metric("👤 Autores", len(ranking))

with c2:
    st.metric(
        "📋 Emendas",
        f"{ranking['quantidade'].sum():,}".replace(",", "."),
    )

with c3:
    st.metric("💼 Empenhado", formatar_moeda_resumida(total_emp))

with c4:
    st.metric("💸 Pago", formatar_moeda_resumida(total_pago))

with c5:
    st.metric(
        "✅ Execução",
        f"{pct_geral:.1f}%".replace(".", ","),
        help="Percentual do valor empenhado que foi efetivamente pago"
    )

st.divider()


# ============================================================
# LAYOUT PRINCIPAL — tabela à esquerda, destinatários à direita
# ============================================================

col_tabela, col_destinos = st.columns([3, 2])

# --------------------------------------------------------
# COLUNA ESQUERDA — tabela do ranking
# --------------------------------------------------------

with col_tabela:
    st.markdown("### 📋 Ranking completo")
    st.caption("Clique em um parlamentar para ver para onde foi a verba →")

    tabela = pd.DataFrame({
        "Pos.":      ranking["posicao"],
        "Autor":     ranking["nomeAutor"].apply(limpar_nome),
        "Tipo":      ranking["tipo"],
        "Emendas":   ranking["quantidade"],
        "Empenhado": ranking["total_empenhado"].apply(formatar_moeda),
        "Pago":      ranking["total_pago"].apply(formatar_moeda),
        "Execução":  ranking["execucao"],
    })

    # on_select="rerun" faz o Streamlit reexecutar quando o usuário
    # seleciona uma linha — é assim que capturamos o clique
    evento = st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True,
        height=520,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Pos.":      st.column_config.NumberColumn(width="small"),
            "Tipo":      st.column_config.TextColumn(width="small"),
            "Emendas":   st.column_config.NumberColumn(width="small"),
            "Execução":  st.column_config.TextColumn(width="small"),
        },
    )

    # Botão de download abaixo da tabela
    csv_download = ranking.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="⬇️ Baixar CSV",
        data=csv_download,
        file_name=f"ranking_emendas_{'_'.join(str(a) for a in sorted(anos_selecionados))}.csv",
        mime="text/csv",
    )


# --------------------------------------------------------
# COLUNA DIREITA — distribuição por área temática (função)
# --------------------------------------------------------

def _grafico_funcao(df_fonte: pd.DataFrame, titulo: str, subtitulo: str):
    """Monta gráfico de barras horizontais por área temática."""
    if "funcao" not in df_fonte.columns:
        st.info("Dados de área temática não disponíveis.")
        return

    por_funcao = (
        df_fonte.groupby("funcao")["valorEmpenhado"]
        .sum()
        .reset_index()
        .sort_values("valorEmpenhado", ascending=False)
        .head(10)
    )
    por_funcao.columns = ["Área", "Empenhado"]
    # Remove entradas vazias ou sem informação
    por_funcao = por_funcao[
        ~por_funcao["Área"].str.strip().isin(["", "Sem informação", "S/I"])
    ]

    if por_funcao.empty:
        st.info("Sem dados de área temática para exibir.")
        return

    st.markdown(f"### {titulo}")
    st.caption(subtitulo)

    # Formata os valores para exibição legível no eixo X
    def _fmt_resumido(v):
        if v >= 1_000_000_000:
            return f"R$ {v/1_000_000_000:.1f} bi".replace(".", ",")
        if v >= 1_000_000:
            return f"R$ {v/1_000_000:.1f} mi".replace(".", ",")
        if v >= 1_000:
            return f"R$ {v/1_000:.0f} mil"
        return f"R$ {v:.0f}"

    por_funcao["valor_fmt"] = por_funcao["Empenhado"].apply(_fmt_resumido)

    fig = px.bar(
        por_funcao,
        x="Empenhado",
        y="Área",
        orientation="h",
        color="Empenhado",
        color_continuous_scale="Blues",
        text="valor_fmt",
        labels={"Empenhado": "", "Área": ""},
    )
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        xaxis={"visible": False},
        height=420,
        plot_bgcolor="white",
        paper_bgcolor="white",
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{text}<extra></extra>",
    )
    st.plotly_chart(fig, use_container_width=True)


with col_destinos:

    linhas_selecionadas = evento.selection.get("rows", [])

    if linhas_selecionadas:
        idx = linhas_selecionadas[0]
        nome_parlamentar = ranking.iloc[idx]["nomeAutor"]
        nome_exibir = limpar_nome(nome_parlamentar)

        df_parl = df[df["nomeAutor"] == nome_parlamentar].copy()
        _grafico_funcao(
            df_parl,
            titulo=f"🎯 {nome_exibir}",
            subtitulo="Distribuição por área temática — valor empenhado",
        )

    else:
        _grafico_funcao(
            df,
            titulo="🎯 Áreas temáticas — geral",
            subtitulo="Top 10 áreas por valor empenhado no período",
        )

st.divider()


# ============================================================
# 3 GRÁFICOS TOP 10 — Empenhado | Pago | % Execução
# ============================================================

st.markdown("### 🏆 Top 10 parlamentares")

top10 = ranking.head(10).copy()
top10["nome_curto"] = top10["nomeAutor"].apply(limpar_nome)

def _fmt_eixo(v):
    """Formata valor para rótulo de barra."""
    if v >= 1_000_000_000:
        return f"R$ {v/1_000_000_000:.1f} bi".replace(".", ",")
    if v >= 1_000_000:
        return f"R$ {v/1_000_000:.1f} mi".replace(".", ",")
    if v >= 1_000:
        return f"R$ {v/1_000:.0f} mil"
    return f"R$ {v:.0f}"

top10["emp_fmt"]  = top10["total_empenhado"].apply(_fmt_eixo)
top10["pago_fmt"] = top10["total_pago"].apply(_fmt_eixo)

graf1, graf2, graf3 = st.columns(3)

# --- Gráfico 1: Empenhado ---
with graf1:
    st.markdown("##### 💼 Valor Empenhado")
    fig1 = px.bar(
        top10.sort_values("total_empenhado"),
        x="total_empenhado",
        y="nome_curto",
        orientation="h",
        text="emp_fmt",
        color_discrete_sequence=["#2e6da4"],
        labels={"total_empenhado": "", "nome_curto": ""},
    )
    fig1.update_layout(
        xaxis={"visible": False},
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=420,
        margin=dict(l=5, r=60, t=10, b=10),
        showlegend=False,
    )
    fig1.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{text}<extra></extra>",
    )
    st.plotly_chart(fig1, use_container_width=True)

# --- Gráfico 2: Pago ---
with graf2:
    st.markdown("##### 💸 Valor Pago")
    fig2 = px.bar(
        top10.sort_values("total_pago"),
        x="total_pago",
        y="nome_curto",
        orientation="h",
        text="pago_fmt",
        color_discrete_sequence=["#27ae60"],
        labels={"total_pago": "", "nome_curto": ""},
    )
    fig2.update_layout(
        xaxis={"visible": False},
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=420,
        margin=dict(l=5, r=60, t=10, b=10),
        showlegend=False,
    )
    fig2.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{text}<extra></extra>",
    )
    st.plotly_chart(fig2, use_container_width=True)

# --- Gráfico 3: % Execução ---
with graf3:
    st.markdown("##### ✅ % Execução")
    top10_exec = top10.sort_values("execucao_pct").copy()
    top10_exec["exec_fmt"] = top10_exec["execucao_pct"].apply(
        lambda v: f"{v:.1f}%".replace(".", ",")
    )
    # Cor por faixa de execução
    def _cor_exec(v):
        if v >= 75:
            return "#27ae60"   # verde — boa execução
        if v >= 40:
            return "#f39c12"   # laranja — execução média
        return "#e74c3c"       # vermelho — baixa execução

    top10_exec["cor"] = top10_exec["execucao_pct"].apply(_cor_exec)

    fig3 = px.bar(
        top10_exec,
        x="execucao_pct",
        y="nome_curto",
        orientation="h",
        text="exec_fmt",
        color="cor",
        color_discrete_map="identity",
        labels={"execucao_pct": "", "nome_curto": ""},
    )
    fig3.update_layout(
        xaxis={"visible": False, "range": [0, 115]},
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=420,
        margin=dict(l=5, r=60, t=10, b=10),
        showlegend=False,
    )
    fig3.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Execução: %{text}<extra></extra>",
    )
    st.plotly_chart(fig3, use_container_width=True)


# ============================================================
# RODAPÉ
# ============================================================

st.divider()

col_rod_esq, col_rod_btn, col_rod_dir = st.columns([3, 2, 3])
with col_rod_btn:
    if st.button("🔄 Atualizar dados (limpar cache)", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown(
    "<p style='text-align:center; color:#999; font-size:0.85rem; margin-top:1rem;'>"
    "Dados obtidos via Portal da Transparência — CGU. "
    "Atualização automática a cada hora."
    "</p>",
    unsafe_allow_html=True
)
