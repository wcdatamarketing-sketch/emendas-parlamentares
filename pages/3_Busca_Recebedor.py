# ============================================================
# pages/3_Busca_Recebedor.py
# Tela de busca por quem RECEBEU as emendas —
# município, estado, ONG, empresa ou entidade específica
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px

# Importamos as funções de cache necessárias para essa tela
from utils.cache import (
    cache_emendas_por_municipio,
    cache_emendas_por_favorecido,
)

# Importamos os formatadores
from utils.formatters import (
    formatar_moeda,
    formatar_moeda_resumida,
    calcular_percentual_execucao,
    limpar_nome,
    valor_ou_traco,
)


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Busca por Recebedor — Emendas",
    page_icon="🔍",
    layout="wide",
)


# ============================================================
# VERIFICAÇÃO DA CHAVE DE API
# ============================================================

if "api_key" not in st.session_state:
    st.error("⚠️ Acesse a plataforma pela página inicial.")
    st.stop()

api_key = st.session_state.api_key


# ============================================================
# CABEÇALHO
# ============================================================

st.markdown(
    "<h1 style='color:#1a3a5c;'>🔍 Busca por Recebedor</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "Descubra quem recebeu recursos de emendas parlamentares — "
    "municípios, estados, ONGs, empresas ou entidades específicas."
)
st.divider()


# ============================================================
# TIPO DE BUSCA
# ============================================================

# radio cria botões de seleção exclusiva (só um pode estar marcado)
# é como uma pergunta de múltipla escolha com uma resposta só
tipo_busca = st.radio(
    "O que você quer buscar?",
    options=["Por município", "Por favorecido (ONG, empresa, entidade)"],
    horizontal=True,  # exibe as opções lado a lado em vez de empilhadas
)

st.divider()


# ============================================================
# BUSCA POR MUNICÍPIO
# ============================================================

if tipo_busca == "Por município":

    st.markdown("### 🏙️ Busca por município")

    # Linha de filtros
    col_municipio, col_uf, col_ano = st.columns([3, 1, 1])

    with col_municipio:
        municipio = st.text_input(
            "Nome do município",
            placeholder="Ex: Brasília, São Paulo, Fortaleza...",
        )

    with col_uf:
        uf = st.selectbox(
            "Estado (UF)",
            options=[
                "Todos", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES",
                "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE",
                "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
            ],
        )

    with col_ano:
        ano = st.selectbox(
            "Ano",
            options=[2024, 2023, 2022],
        )

    # Só executa se o usuário digitou o nome do município
    if not municipio:
        st.info("👆 Digite o nome de um município para começar.")
        st.stop()

    # Busca os dados com cache
    with st.spinner(f"Buscando emendas destinadas a {municipio}..."):
        emendas_raw = cache_emendas_por_municipio(api_key, municipio, ano)

    if not emendas_raw:
        st.warning(
            f"Nenhuma emenda encontrada para '{municipio}' em {ano}. "
            "Verifique o nome e tente novamente."
        )
        st.stop()

    # Converte para DataFrame
    df = pd.DataFrame(emendas_raw)

    # Garante que as colunas de valor são numéricas
    for coluna in ["valorEmpenhado", "valorPago"]:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0)

    # Aplica filtro de UF se selecionado
    if uf != "Todos" and "ufFavorecido" in df.columns:
        df = df[df["ufFavorecido"] == uf]

    if df.empty:
        st.warning("Nenhum resultado encontrado com os filtros aplicados.")
        st.stop()

    # --------------------------------------------------------
    # CARDS DE RESUMO
    # --------------------------------------------------------

    st.markdown(f"### 📈 Resumo — {limpar_nome(municipio)}")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Total de emendas", len(df))
    with c2:
        st.metric(
            "Total empenhado",
            formatar_moeda_resumida(df["valorEmpenhado"].sum())
        )
    with c3:
        total_pago = df["valorPago"].sum() if "valorPago" in df.columns else 0
        st.metric("Total pago", formatar_moeda_resumida(total_pago))
    with c4:
        st.metric(
            "Parlamentares envolvidos",
            # nunique() conta quantos valores únicos existem na coluna
            # é como o CONT.SE do Excel contando valores distintos
            df["nomeAutor"].nunique() if "nomeAutor" in df.columns else "—"
        )

    st.divider()

    # --------------------------------------------------------
    # GRÁFICO — QUEM MAIS DESTINOU EMENDAS PARA ESSE MUNICÍPIO
    # --------------------------------------------------------

    st.markdown("#### 🏆 Parlamentares que mais destinaram emendas")

    if "nomeAutor" in df.columns:

        # Agrupa por parlamentar e soma os valores
        por_parlamentar = df.groupby("nomeAutor").agg(
            total=("valorEmpenhado", "sum"),
            quantidade=("valorEmpenhado", "count"),
            partido=("partidoAutor", "first"),
        ).reset_index()

        por_parlamentar = por_parlamentar.sort_values("total", ascending=False).head(15)

        fig = px.bar(
            por_parlamentar,
            x="total",
            y="nomeAutor",
            orientation="h",
            color="partido",   # cada partido com uma cor diferente
            hover_data=["quantidade", "partido"],
            labels={
                "total": "Total Empenhado (R$)",
                "nomeAutor": "Parlamentar",
                "partido": "Partido",
                "quantidade": "Nº de Emendas",
            },
        )
        fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            height=500,
            plot_bgcolor="white",
            margin=dict(l=200),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --------------------------------------------------------
    # TABELA COMPLETA
    # --------------------------------------------------------

    st.markdown("#### 📋 Lista de emendas recebidas")

    colunas_disponiveis = {
        "nomeAutor": "Parlamentar",
        "partidoAutor": "Partido",
        "tipoEmenda": "Tipo de Emenda",
        "funcao": "Área Temática",
        "nomeFavorecido": "Favorecido",
        "valorEmpenhado": "Empenhado",
        "valorPago": "Pago",
    }

    colunas_existentes = {
        k: v for k, v in colunas_disponiveis.items() if k in df.columns
    }

    tabela = df[list(colunas_existentes.keys())].copy()
    tabela.columns = list(colunas_existentes.values())

    if "Empenhado" in tabela.columns:
        tabela["Empenhado"] = tabela["Empenhado"].apply(formatar_moeda)
    if "Pago" in tabela.columns:
        tabela["Pago"] = tabela["Pago"].apply(formatar_moeda)
    if "Parlamentar" in tabela.columns:
        tabela["Parlamentar"] = tabela["Parlamentar"].apply(limpar_nome)

    st.dataframe(tabela, use_container_width=True, hide_index=True, height=400)

    # Botão de download
    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="⬇️ Baixar dados em CSV",
        data=csv,
        file_name=f"emendas_{municipio.replace(' ', '_')}_{ano}.csv",
        mime="text/csv",
    )


# ============================================================
# BUSCA POR FAVORECIDO
# ============================================================

else:

    st.markdown("### 🏢 Busca por favorecido")
    st.caption(
        "Favorecido é quem recebeu o recurso — pode ser uma ONG, "
        "empresa, prefeitura, fundo público ou pessoa física."
    )

    col_favorecido, col_ano = st.columns([3, 1])

    with col_favorecido:
        nome_favorecido = st.text_input(
            "Nome do favorecido",
            placeholder="Ex: Associação, Fundação, Hospital...",
        )

    with col_ano:
        ano = st.selectbox(
            "Ano",
            options=[2024, 2023, 2022],
            key="ano_favorecido",
            # key é necessário quando há dois widgets do mesmo tipo na tela
            # o Streamlit usa o key para diferenciar um do outro
        )

    if not nome_favorecido:
        st.info("👆 Digite o nome do favorecido para começar.")
        st.stop()

    with st.spinner(f"Buscando emendas recebidas por '{nome_favorecido}'..."):
        emendas_raw = cache_emendas_por_favorecido(api_key, nome_favorecido, ano)

    if not emendas_raw:
        st.warning(
            f"Nenhuma emenda encontrada para '{nome_favorecido}' em {ano}."
        )
        st.stop()

    df = pd.DataFrame(emendas_raw)

    for coluna in ["valorEmpenhado", "valorPago"]:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0)

    # --------------------------------------------------------
    # CARDS DE RESUMO
    # --------------------------------------------------------

    st.markdown(f"### 📈 Resumo — {limpar_nome(nome_favorecido)}")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Total de emendas recebidas", len(df))
    with c2:
        st.metric(
            "Total empenhado",
            formatar_moeda_resumida(df["valorEmpenhado"].sum())
        )
    with c3:
        total_pago = df["valorPago"].sum() if "valorPago" in df.columns else 0
        st.metric("Total pago", formatar_moeda_resumida(total_pago))
    with c4:
        st.metric(
            "Parlamentares envolvidos",
            df["nomeAutor"].nunique() if "nomeAutor" in df.columns else "—"
        )

    st.divider()

    # --------------------------------------------------------
    # GRÁFICO — DISTRIBUIÇÃO POR ÁREA TEMÁTICA
    # --------------------------------------------------------

    if "funcao" in df.columns:

        st.markdown("#### 🎯 Distribuição por área temática")

        por_area = df.groupby("funcao")["valorEmpenhado"].sum().reset_index()
        por_area.columns = ["Área", "Valor"]
        por_area = por_area.sort_values("Valor", ascending=False)

        fig = px.pie(
            por_area,
            names="Área",
            values="Valor",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Blues_r,
        )
        fig.update_layout(height=350, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

    # --------------------------------------------------------
    # TABELA COMPLETA
    # --------------------------------------------------------

    st.markdown("#### 📋 Lista de emendas recebidas")

    colunas_disponiveis = {
        "nomeAutor": "Parlamentar",
        "partidoAutor": "Partido",
        "ufAutor": "UF Parlamentar",
        "tipoEmenda": "Tipo de Emenda",
        "funcao": "Área Temática",
        "municipioFavorecido": "Município",
        "ufFavorecido": "UF",
        "valorEmpenhado": "Empenhado",
        "valorPago": "Pago",
    }

    colunas_existentes = {
        k: v for k, v in colunas_disponiveis.items() if k in df.columns
    }

    tabela = df[list(colunas_existentes.keys())].copy()
    tabela.columns = list(colunas_existentes.values())

    if "Empenhado" in tabela.columns:
        tabela["Empenhado"] = tabela["Empenhado"].apply(formatar_moeda)
    if "Pago" in tabela.columns:
        tabela["Pago"] = tabela["Pago"].apply(formatar_moeda)
    if "Parlamentar" in tabela.columns:
        tabela["Parlamentar"] = tabela["Parlamentar"].apply(limpar_nome)

    st.dataframe(tabela, use_container_width=True, hide_index=True, height=400)

    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="⬇️ Baixar dados em CSV",
        data=csv,
        file_name=f"emendas_{nome_favorecido.replace(' ', '_')}_{ano}.csv",
        mime="text/csv",
    )
