import streamlit as st
import pandas as pd
import plotly.express as px
import requests as req_teste

from utils.cache import cache_emendas_ranking
from utils.formatters import (
    formatar_moeda,
    formatar_moeda_resumida,
    calcular_percentual_execucao,
    limpar_nome,
    valor_ou_traco,
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
# TESTE TEMPORÁRIO — vamos ver o que a API responde
# ============================================================
r = req_teste.get(
    "https://api.portaldatransparencia.gov.br/api-de-dados/emendas-parlamentares",
    params={"ano": 2024, "pagina": 1},
    headers={"chave-api-dados": api_key.strip(), "Accept": "application/json"},
    timeout=15,
)
st.write(f"**Status HTTP:** {r.status_code}")
st.write(f"**Chave usada (primeiros 8 caracteres):** {api_key[:8]}...")
st.write(f"**Resposta da API:** {r.text[:500]}")
st.stop()
