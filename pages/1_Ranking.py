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
# FILTROS
# ============================================================

ANOS_DISPONIVEIS = [2026, 2025, 2024, 2023]

col_ano, col_tipo, col_local = st.columns([2, 2, 2])

with col_ano:
    anos_selecionados = st.multiselect(
        "Anos (selecione um ou mais)",
        options=ANOS_DISPONIVEIS,
        default=ANOS_DISPONIVEIS,
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

if not anos_selecionados:
    st.warning("⚠️ Selecione pelo menos um ano para visualizar o ranking.")
    st.stop()


# ============================================================
# BUSCA DOS DADOS
# ============================================================

anos_ordenados = sorted(anos_selecionados)
todas_emendas = []

with st.spinner(f"Buscando dados de {len(anos_ordenados)} ano(s)..."):
    for ano_atual in anos_ordenados:
        try:
            emendas_do_ano = cache_emendas_ranking(api_key, ano_atual)
            for emenda in emendas_do_ano:
                emenda["ano"] = ano_atual
            todas_emendas.extend(emendas_do_ano)
        except Exception as e:
            st.error(f"Erro ao buscar dados de {ano_atual}: {str(e)}")
            st.stop()

if not todas_emendas:
    st.warning("Nenhum dado encontrado nos anos selecionados.")
    st.stop()


# ============================================================
# PROCESSAMENTO
# ============================================================

df = pd.DataFrame(todas_emendas)

colunas_valor = [
    "valorEmpenhado", "valorLiquidado", "valorPago",
    "valorRestoInscrito", "valorRestoCancelado", "valorRestoPago"
]
for coluna in colunas_valor:
    if coluna in df.columns:
        df[coluna] = (
            df[coluna].astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0)

# Aplica tipo resumido no DataFrame bruto também (para filtro funcionar)
if "tipoEmenda" in df.columns:
    df["tipoResumido"] = df["tipoEmenda"].apply(resumir_tipo)


# ============================================================
# FILTROS
# ============================================================

if tipo_emenda != "Todas" and "tipoResumido" in df.columns:
    df = df[df["tipoResumido"] == tipo_emenda]

if localidade and "localidadeDoGasto" in df.columns:
    df = df[df["localidadeDoGasto"].str.contains(localidade, case=False, na=False)]

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
# COLUNA DIREITA — top 10 destinatários
# --------------------------------------------------------

with col_destinos:

    # Verifica se o usuário clicou em alguma linha
    linhas_selecionadas = evento.selection.get("rows", [])

    if linhas_selecionadas:
        # Usuário clicou numa linha — pega o índice e o nome do parlamentar
        idx = linhas_selecionadas[0]
        nome_parlamentar = ranking.iloc[idx]["nomeAutor"]
        nome_exibir = limpar_nome(nome_parlamentar)

        st.markdown(f"### 📍 Destinos — {nome_exibir}")
        st.caption("Top 10 municípios por valor empenhado")

        # Filtra o DataFrame bruto pelo parlamentar selecionado
        df_parl = df[df["nomeAutor"] == nome_parlamentar].copy()

        col_destino = None
        for c in ["municipioFavorecido", "localidadeDoGasto"]:
            if c in df_parl.columns:
                col_destino = c
                break

        if col_destino:
            destinos = (
                df_parl.groupby(col_destino)["valorEmpenhado"]
                .sum()
                .reset_index()
                .sort_values("valorEmpenhado", ascending=False)
                .head(10)
            )
            destinos.columns = ["Destino", "Empenhado"]
            destinos = destinos[destinos["Destino"].str.strip() != ""]

            fig_dest = px.bar(
                destinos,
                x="Empenhado",
                y="Destino",
                orientation="h",
                color="Empenhado",
                color_continuous_scale="Blues",
                labels={"Empenhado": "R$ Empenhado", "Destino": ""},
            )
            fig_dest.update_layout(
                yaxis={"categoryorder": "total ascending"},
                height=420,
                plot_bgcolor="white",
                paper_bgcolor="white",
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=10, b=10),
            )
            fig_dest.update_traces(
                hovertemplate="<b>%{y}</b><br>R$ %{x:,.0f}<extra></extra>"
            )
            st.plotly_chart(fig_dest, use_container_width=True)
        else:
            st.info("Dados de destino não disponíveis para este parlamentar.")

    else:
        # Nenhuma linha selecionada — mostra top 10 geral
        st.markdown("### 🗺️ Top 10 destinos geral")
        st.caption("Municípios que mais receberam emendas no período")

        col_destino = None
        for c in ["municipioFavorecido", "localidadeDoGasto"]:
            if c in df.columns:
                col_destino = c
                break

        if col_destino:
            destinos_geral = (
                df.groupby(col_destino)["valorEmpenhado"]
                .sum()
                .reset_index()
                .sort_values("valorEmpenhado", ascending=False)
                .head(10)
            )
            destinos_geral.columns = ["Destino", "Empenhado"]
            destinos_geral = destinos_geral[
                destinos_geral["Destino"].str.strip() != ""
            ]

            fig_geral = px.bar(
                destinos_geral,
                x="Empenhado",
                y="Destino",
                orientation="h",
                color="Empenhado",
                color_continuous_scale="Blues",
                labels={"Empenhado": "R$ Empenhado", "Destino": ""},
            )
            fig_geral.update_layout(
                yaxis={"categoryorder": "total ascending"},
                height=420,
                plot_bgcolor="white",
                paper_bgcolor="white",
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=10, b=10),
            )
            fig_geral.update_traces(
                hovertemplate="<b>%{y}</b><br>R$ %{x:,.0f}<extra></extra>"
            )
            st.plotly_chart(fig_geral, use_container_width=True)

st.divider()


# ============================================================
# GRÁFICO TOP 20
# ============================================================

st.markdown("### 🏆 Top 20 por valor empenhado")

top20 = ranking.head(20).copy()
top20["nome_curto"] = top20["nomeAutor"].apply(limpar_nome)

fig = px.bar(
    top20,
    x="total_empenhado",
    y="nome_curto",
    orientation="h",
    color="tipo",
    hover_data={"quantidade": True, "execucao": True, "periodo": True, "nome_curto": False},
    labels={
        "total_empenhado": "Empenhado (R$)",
        "nome_curto": "",
        "tipo": "Tipo",
        "execucao": "Execução",
        "periodo": "Período",
        "quantidade": "Emendas",
    },
    color_discrete_sequence=px.colors.qualitative.Set2,
)
fig.update_layout(
    yaxis={"categoryorder": "total ascending"},
    height=600,
    showlegend=True,
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=20, r=20, t=20, b=20),
    legend=dict(title="Tipo", orientation="h", y=-0.15),
)
fig.update_traces(
    hovertemplate="<b>%{y}</b><br>Empenhado: R$ %{x:,.0f}<extra></extra>"
)
st.plotly_chart(fig, use_container_width=True)


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
