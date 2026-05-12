# ============================================================
# pages/4_Comparativo.py
# Comparação entre dois deputados OU dois partidos
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.cache import (
    cache_emendas_ranking,
    cache_deputados_legislatura,
    cache_partidos_legislatura,
    cache_leis_aprovadas,
    cache_relatorias_aprovadas,
    cache_votacoes_do_deputado,
    cache_votacoes_do_partido,
)
from utils.formatters import (
    formatar_moeda,
    formatar_moeda_resumida,
    limpar_nome,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Comparativo — Emendas Parlamentares",
    page_icon="⚖️",
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
# CABEÇALHO
# ============================================================

st.markdown(
    "<h1 style='color:#1a3a5c;'>⚖️ Comparativo</h1>",
    unsafe_allow_html=True,
)
st.markdown("Compare dois deputados ou dois partidos lado a lado.")
st.divider()


# ============================================================
# MODO DE COMPARAÇÃO
# ============================================================

modo = st.radio(
    "O que você quer comparar?",
    options=["👤 Deputado vs Deputado", "🏛️ Partido vs Partido"],
    horizontal=True,
)
modo_partido = modo.startswith("🏛️")

st.divider()


# ============================================================
# ANOS — checkboxes igual ao Ranking
# ============================================================

st.markdown("**Anos**")
col_2023, col_2024, col_2025, col_2026, col_esp = st.columns([1, 1, 1, 1, 4])
with col_2023:
    ano_2023 = st.checkbox("2023", value=True, key="comp_2023")
with col_2024:
    ano_2024 = st.checkbox("2024", value=True, key="comp_2024")
with col_2025:
    ano_2025 = st.checkbox("2025", value=True, key="comp_2025")
with col_2026:
    ano_2026 = st.checkbox("2026", value=True, key="comp_2026")

anos_selecionados = [
    a for a, sel in [
        (2023, ano_2023), (2024, ano_2024),
        (2025, ano_2025), (2026, ano_2026),
    ] if sel
]

if not anos_selecionados:
    st.warning("⚠️ Selecione pelo menos um ano.")
    st.stop()


# ============================================================
# CARREGA BASE DE EMENDAS (todos os anos, filtra depois)
# ============================================================

with st.spinner("Carregando base de emendas..."):
    todas_emendas = []
    for ano in anos_selecionados:
        try:
            lote = cache_emendas_ranking(api_key, ano)
            for e in lote:
                e["ano"] = ano
            todas_emendas.extend(lote)
        except Exception as ex:
            st.error(f"Erro ao carregar {ano}: {ex}")
            st.stop()

if not todas_emendas:
    st.warning("Nenhum dado encontrado.")
    st.stop()

df_base = pd.DataFrame(todas_emendas)

# Garante colunas numéricas
for col in ["valorEmpenhado", "valorPago", "valorLiquidado"]:
    if col in df_base.columns:
        if not pd.api.types.is_numeric_dtype(df_base[col]):
            df_base[col] = (
                df_base[col].astype(str)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            df_base[col] = pd.to_numeric(df_base[col], errors="coerce").fillna(0)
        else:
            df_base[col] = df_base[col].fillna(0)


# ============================================================
# SELECTS — DEPUTADO OU PARTIDO
# ============================================================

st.markdown("---")

if not modo_partido:

    # --- Modo Deputado ---
    with st.spinner("Carregando lista de deputados..."):
        deputados = cache_deputados_legislatura(57)

    # Monta dicionário nome → id para o select
    dep_dict = {
        f"{limpar_nome(d.get('nome',''))} ({d.get('siglaPartido','')}-{d.get('siglaUf','')})": d
        for d in deputados if d.get("nome")
    }
    opcoes_dep = sorted(dep_dict.keys())

    col_a, col_vs, col_b = st.columns([5, 1, 5])
    with col_a:
        st.markdown("#### 🔵 Deputado A")
        sel_a = st.selectbox("Selecione", opcoes_dep, key="dep_a",
                             index=0, placeholder="Escolha um deputado...")
    with col_vs:
        st.markdown("<br><br><h2 style='text-align:center;color:#999'>VS</h2>",
                    unsafe_allow_html=True)
    with col_b:
        st.markdown("#### 🔴 Deputado B")
        sel_b = st.selectbox("Selecione", opcoes_dep, key="dep_b",
                             index=min(1, len(opcoes_dep)-1),
                             placeholder="Escolha um deputado...")

    if sel_a == sel_b:
        st.warning("Selecione deputados diferentes para comparar.")
        st.stop()

    dep_a = dep_dict[sel_a]
    dep_b = dep_dict[sel_b]
    label_a = limpar_nome(dep_a.get("nome", ""))
    label_b = limpar_nome(dep_b.get("nome", ""))
    id_a = dep_a.get("id")
    id_b = dep_b.get("id")

else:

    # --- Modo Partido ---
    with st.spinner("Carregando lista de partidos..."):
        partidos = cache_partidos_legislatura(57)

    col_a, col_vs, col_b = st.columns([5, 1, 5])
    with col_a:
        st.markdown("#### 🔵 Partido A")
        partido_a = st.selectbox("Selecione", partidos, key="part_a", index=0)
    with col_vs:
        st.markdown("<br><br><h2 style='text-align:center;color:#999'>VS</h2>",
                    unsafe_allow_html=True)
    with col_b:
        st.markdown("#### 🔴 Partido B")
        partido_b = st.selectbox("Selecione", partidos, key="part_b",
                                 index=min(1, len(partidos)-1))

    if partido_a == partido_b:
        st.warning("Selecione partidos diferentes para comparar.")
        st.stop()

    label_a = partido_a
    label_b = partido_b
    id_a = None
    id_b = None


st.divider()


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def emendas_de(identificador, modo_partido: bool, df: pd.DataFrame) -> pd.DataFrame:
    """Filtra o DataFrame pelo deputado (nome) ou partido."""
    if modo_partido:
        col = "partidoAutor" if "partidoAutor" in df.columns else None
        if col:
            return df[df[col].str.upper() == identificador.upper()].copy()
        return pd.DataFrame()
    else:
        if "nomeAutor" not in df.columns:
            return pd.DataFrame()
        nome_api = identificador  # label_a/b já é o nome limpo
        return df[
            df["nomeAutor"].apply(limpar_nome).str.upper() == nome_api.upper()
        ].copy()


def resumo_emendas(df: pd.DataFrame) -> dict:
    """Calcula métricas consolidadas de um conjunto de emendas."""
    if df.empty:
        return {"empenhado": 0, "pago": 0, "quantidade": 0, "execucao": 0.0}
    emp  = df["valorEmpenhado"].sum() if "valorEmpenhado" in df.columns else 0
    pago = df["valorPago"].sum()      if "valorPago"      in df.columns else 0
    pct  = min((pago / emp * 100) if emp > 0 else 0, 100.0)
    return {
        "empenhado":  emp,
        "pago":       pago,
        "quantidade": len(df),
        "execucao":   pct,
    }


def grafico_funcao(df: pd.DataFrame, cor: str) -> None:
    """Gráfico de barras por área temática."""
    if "funcao" not in df.columns or df.empty:
        st.info("Sem dados de área temática.")
        return
    por_funcao = (
        df.groupby("funcao")["valorEmpenhado"].sum()
        .reset_index()
        .sort_values("valorEmpenhado", ascending=False)
        .head(8)
    )
    por_funcao.columns = ["Área", "Empenhado"]
    por_funcao = por_funcao[
        ~por_funcao["Área"].str.strip().isin(["", "Sem informação", "S/I"])
    ]
    if por_funcao.empty:
        st.info("Sem dados.")
        return

    def _fmt(v):
        if v >= 1_000_000_000:
            return f"R$ {v/1_000_000_000:.1f} bi".replace(".", ",")
        if v >= 1_000_000:
            return f"R$ {v/1_000_000:.1f} mi".replace(".", ",")
        return f"R$ {v/1_000:.0f} mil"

    por_funcao["fmt"] = por_funcao["Empenhado"].apply(_fmt)

    fig = px.bar(
        por_funcao, x="Empenhado", y="Área", orientation="h",
        text="fmt", color_discrete_sequence=[cor],
        labels={"Empenhado": "", "Área": ""},
    )
    fig.update_layout(
        xaxis={"visible": False}, yaxis={"categoryorder": "total ascending"},
        height=320, plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=5, r=80, t=5, b=5), showlegend=False,
    )
    fig.update_traces(textposition="outside",
                      hovertemplate="<b>%{y}</b><br>%{text}<extra></extra>")
    st.plotly_chart(fig, use_container_width=True)


def grafico_favorecidos(df: pd.DataFrame, cor: str) -> None:
    """Top 8 favorecidos por valor empenhado."""
    col = next((c for c in ["nomeFavorecido", "municipioFavorecido",
                             "localidadeDoGasto"] if c in df.columns), None)
    if not col or df.empty:
        st.info("Sem dados de favorecidos.")
        return
    top = (
        df.groupby(col)["valorEmpenhado"].sum()
        .reset_index()
        .sort_values("valorEmpenhado", ascending=False)
        .head(8)
    )
    top.columns = ["Favorecido", "Empenhado"]
    top = top[~top["Favorecido"].str.strip().isin(["", "Sem informação", "S/I"])]
    if top.empty:
        st.info("Sem dados.")
        return

    def _fmt(v):
        if v >= 1_000_000_000:
            return f"R$ {v/1_000_000_000:.1f} bi".replace(".", ",")
        if v >= 1_000_000:
            return f"R$ {v/1_000_000:.1f} mi".replace(".", ",")
        return f"R$ {v/1_000:.0f} mil"

    top["fmt"] = top["Empenhado"].apply(_fmt)

    fig = px.bar(
        top, x="Empenhado", y="Favorecido", orientation="h",
        text="fmt", color_discrete_sequence=[cor],
        labels={"Empenhado": "", "Favorecido": ""},
    )
    fig.update_layout(
        xaxis={"visible": False}, yaxis={"categoryorder": "total ascending"},
        height=320, plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=5, r=80, t=5, b=5), showlegend=False,
    )
    fig.update_traces(textposition="outside",
                      hovertemplate="<b>%{y}</b><br>%{text}<extra></extra>")
    st.plotly_chart(fig, use_container_width=True)


def card_lei(lei: dict) -> None:
    """Exibe um card de lei aprovada."""
    tipo   = lei.get("siglaTipo", "PL")
    numero = lei.get("numero", "")
    ano    = lei.get("ano", "")
    ementa = lei.get("ementa", "Sem ementa disponível")
    ementa_curta = ementa[:120] + "..." if len(ementa) > 120 else ementa
    st.markdown(
        f"<div style='background:#f0f4f8;border-left:4px solid #2e6da4;"
        f"padding:8px 12px;border-radius:4px;margin-bottom:6px;font-size:0.85rem'>"
        f"<b>{tipo} {numero}/{ano}</b><br>{ementa_curta}</div>",
        unsafe_allow_html=True,
    )


def painel_votacoes(votos: list, label: str) -> None:
    """Cards de resumo de votações nominais."""
    if not votos:
        st.info("Sem votações nominais no período.")
        return
    contagem = {"SIM": 0, "NÃO": 0, "ABSTENÇÃO": 0, "OUTROS": 0}
    for v in votos:
        tv = v.get("tipoVoto", "").strip().upper()
        if tv == "SIM":
            contagem["SIM"] += 1
        elif tv in ("NÃO", "NAO"):
            contagem["NÃO"] += 1
        elif tv in ("ABSTENÇÃO", "ABSTENCAO"):
            contagem["ABSTENÇÃO"] += 1
        else:
            contagem["OUTROS"] += 1
    total = sum(contagem.values())
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(_card("✅ Sim",       f"{contagem['SIM']} ({contagem['SIM']/total*100:.0f}%)" if total else "0"), unsafe_allow_html=True)
    c2.markdown(_card("❌ Não",       f"{contagem['NÃO']} ({contagem['NÃO']/total*100:.0f}%)" if total else "0"), unsafe_allow_html=True)
    c3.markdown(_card("➖ Abstenção", f"{contagem['ABSTENÇÃO']} ({contagem['ABSTENÇÃO']/total*100:.0f}%)" if total else "0"), unsafe_allow_html=True)
    c4.markdown(_card("📋 Total",     str(total)), unsafe_allow_html=True)


# ============================================================
# BUSCA DOS DADOS
# ============================================================

# Emendas
df_a = emendas_de(label_a, modo_partido, df_base)
df_b = emendas_de(label_b, modo_partido, df_base)

res_a = resumo_emendas(df_a)
res_b = resumo_emendas(df_b)

# Leis e votações — só para modo deputado (precisa do ID)
leis_autor_a = leis_autor_b = []
leis_relator_a = leis_relator_b = []
votos_a = votos_b = []

if not modo_partido and id_a and id_b:
    ano_i = min(anos_selecionados)
    ano_f = max(anos_selecionados)
    with st.spinner("Buscando dados legislativos..."):
        leis_autor_a   = cache_leis_aprovadas(id_a, ano_i, ano_f)
        leis_autor_b   = cache_leis_aprovadas(id_b, ano_i, ano_f)
        leis_relator_a = cache_relatorias_aprovadas(id_a, ano_i, ano_f)
        leis_relator_b = cache_relatorias_aprovadas(id_b, ano_i, ano_f)
        votos_a        = cache_votacoes_do_deputado(id_a, ano_i, ano_f)
        votos_b        = cache_votacoes_do_deputado(id_b, ano_i, ano_f)

elif modo_partido:
    ano_i = min(anos_selecionados)
    ano_f = max(anos_selecionados)
    with st.spinner("Buscando votações dos partidos (pode demorar)..."):
        votos_partido_a = cache_votacoes_do_partido(label_a, 57, ano_i, ano_f)
        votos_partido_b = cache_votacoes_do_partido(label_b, 57, ano_i, ano_f)


# ============================================================
# CABEÇALHO DOS COMPARADOS
# ============================================================

col_ha, col_hb = st.columns(2)

with col_ha:
    st.markdown(
        f"<div style='background:#e8f0fa;padding:1rem;border-radius:8px;"
        f"border-left:5px solid #2e6da4;'>"
        f"<h3 style='color:#1a3a5c;margin:0'>🔵 {label_a}</h3></div>",
        unsafe_allow_html=True,
    )

with col_hb:
    st.markdown(
        f"<div style='background:#faeaea;padding:1rem;border-radius:8px;"
        f"border-left:5px solid #c0392b;'>"
        f"<h3 style='color:#7b1a1a;margin:0'>🔴 {label_b}</h3></div>",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# CARDS DE MÉTRICAS
# ============================================================

st.markdown("### 📊 Emendas")
col_m1, col_m2 = st.columns(2)

def _card(titulo: str, valor: str) -> str:
    """Gera HTML de um card de métrica com fonte reduzida."""
    return (
        f"<div style='background:#f0f4f8;border:1px solid #d0dce8;"
        f"border-radius:8px;padding:10px 14px;text-align:center'>"
        f"<div style='color:#666;font-size:0.72rem;margin-bottom:4px'>{titulo}</div>"
        f"<div style='color:#1a3a5c;font-size:1.05rem;font-weight:600'>{valor}</div>"
        f"</div>"
    )

def _cards_metricas(res: dict, label: str, emoji: str) -> None:
    pct = f"{res['execucao']:.1f}%".replace(".", ",")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(_card(f"{emoji} Emendas",  str(res["quantidade"])),        unsafe_allow_html=True)
    c2.markdown(_card("💼 Empenhado", formatar_moeda_resumida(res["empenhado"])), unsafe_allow_html=True)
    c3.markdown(_card("💸 Pago",      formatar_moeda_resumida(res["pago"])),      unsafe_allow_html=True)
    c4.markdown(_card("✅ Execução",  pct),                                       unsafe_allow_html=True)

with col_m1:
    st.markdown(f"**🔵 {label_a}**")
    _cards_metricas(res_a, label_a, "🔵")

with col_m2:
    st.markdown(f"**🔴 {label_b}**")
    _cards_metricas(res_b, label_b, "🔴")

st.divider()


# ============================================================
# ÁREAS TEMÁTICAS
# ============================================================

st.markdown("### 🎯 Distribuição por área temática")
col_fa, col_fb = st.columns(2)

with col_fa:
    st.markdown(f"**🔵 {label_a}**")
    grafico_funcao(df_a, "#2e6da4")

with col_fb:
    st.markdown(f"**🔴 {label_b}**")
    grafico_funcao(df_b, "#c0392b")

st.divider()


# ============================================================
# PRINCIPAIS FAVORECIDOS
# ============================================================

st.markdown("### 🏢 Principais favorecidos")
col_fava, col_favb = st.columns(2)

with col_fava:
    st.markdown(f"**🔵 {label_a}**")
    grafico_favorecidos(df_a, "#2e6da4")

with col_favb:
    st.markdown(f"**🔴 {label_b}**")
    grafico_favorecidos(df_b, "#c0392b")

st.divider()


# ============================================================
# LEIS APROVADAS — só modo deputado
# ============================================================

if not modo_partido:
    st.markdown("### 🏛️ Leis aprovadas no período")
    col_la, col_lb = st.columns(2)

    with col_la:
        st.markdown(f"**🔵 {label_a}**")
        total_a = len(leis_autor_a) + len(leis_relator_a)
        st.caption(f"Como autor: {len(leis_autor_a)} | Como relator: {len(leis_relator_a)} | Total: {total_a}")
        if leis_autor_a:
            st.markdown("**Como autor:**")
            for lei in leis_autor_a[:5]:
                card_lei(lei)
        if leis_relator_a:
            st.markdown("**Como relator:**")
            for lei in leis_relator_a[:5]:
                card_lei(lei)
        if not leis_autor_a and not leis_relator_a:
            st.info("Nenhuma lei aprovada encontrada no período.")

    with col_lb:
        st.markdown(f"**🔴 {label_b}**")
        total_b = len(leis_autor_b) + len(leis_relator_b)
        st.caption(f"Como autor: {len(leis_autor_b)} | Como relator: {len(leis_relator_b)} | Total: {total_b}")
        if leis_autor_b:
            st.markdown("**Como autor:**")
            for lei in leis_autor_b[:5]:
                card_lei(lei)
        if leis_relator_b:
            st.markdown("**Como relator:**")
            for lei in leis_relator_b[:5]:
                card_lei(lei)
        if not leis_autor_b and not leis_relator_b:
            st.info("Nenhuma lei aprovada encontrada no período.")

    st.divider()


# ============================================================
# VOTAÇÕES NOMINAIS
# ============================================================

st.markdown("### 🗳️ Votações nominais")

if not modo_partido:
    col_va, col_vb = st.columns(2)
    with col_va:
        st.markdown(f"**🔵 {label_a}**")
        painel_votacoes(votos_a, label_a)
    with col_vb:
        st.markdown(f"**🔴 {label_b}**")
        painel_votacoes(votos_b, label_b)

else:
    # Modo partido — mostra totais agregados
    col_va, col_vb = st.columns(2)

    def _cards_votos_partido(votos: dict, label: str) -> None:
        if not votos:
            st.info("Sem dados de votações.")
            return
        total = votos.get("total_votos", 0)
        deps  = votos.get("deputados", 0)
        st.caption(f"{deps} deputados | {total} votos registrados")
        c1, c2, c3 = st.columns(3)
        sim = votos.get("total_sim", 0)
        nao = votos.get("total_nao", 0)
        abst = votos.get("total_abstencao", 0)
        c1.markdown(_card("✅ Sim",       f"{sim} ({sim/total*100:.0f}%)"   if total else "0"), unsafe_allow_html=True)
        c2.markdown(_card("❌ Não",       f"{nao} ({nao/total*100:.0f}%)"   if total else "0"), unsafe_allow_html=True)
        c3.markdown(_card("➖ Abstenção", f"{abst} ({abst/total*100:.0f}%)" if total else "0"), unsafe_allow_html=True)

    with col_va:
        st.markdown(f"**🔵 {label_a}**")
        _cards_votos_partido(votos_partido_a, label_a)

    with col_vb:
        st.markdown(f"**🔴 {label_b}**")
        _cards_votos_partido(votos_partido_b, label_b)


# ============================================================
# RODAPÉ
# ============================================================

st.divider()
col_r1, col_r2, col_r3 = st.columns([3, 2, 3])
with col_r2:
    if st.button("🔄 Limpar cache", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown(
    "<p style='text-align:center;color:#999;font-size:0.85rem;margin-top:1rem'>"
    "Dados: Portal da Transparência (emendas) e API da Câmara dos Deputados (leis e votações)."
    "</p>",
    unsafe_allow_html=True,
)
