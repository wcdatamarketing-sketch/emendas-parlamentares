# ============================================================
# pages/99_Debug_Votacoes.py
# Página TEMPORÁRIA de diagnóstico — remover após os testes
# ============================================================

import io
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Debug Votações", page_icon="🔬", layout="wide")
st.title("🔬 Debug — CSVs de Votações da Câmara")
st.caption("Página temporária de diagnóstico. Remover após os testes.")
st.divider()

URL_VOTACOES = "https://dadosabertos.camara.leg.br/arquivos/votacoes/csv/votacoes-{ano}.csv"
URL_VOTOS    = "https://dadosabertos.camara.leg.br/arquivos/votacoesVotos/csv/votacoesVotos-{ano}.csv"
API_BASE     = "https://dadosabertos.camara.leg.br/api/v2"


# ============================================================
# HELPERS
# ============================================================

def baixar_csv(url: str, timeout: int = 120) -> pd.DataFrame | None:
    try:
        resp = requests.get(url, timeout=timeout)
        st.caption(f"HTTP {resp.status_code} | {len(resp.content):,} bytes | URL: {url}")
        if resp.status_code != 200:
            st.error(f"Erro HTTP {resp.status_code}")
            return None
        for sep in [";", ","]:
            for enc in ["utf-8", "latin-1", "utf-8-sig"]:
                try:
                    df = pd.read_csv(
                        io.BytesIO(resp.content),
                        sep=sep, encoding=enc,
                        dtype=str, low_memory=False,
                    )
                    if len(df.columns) > 3:
                        df.columns = df.columns.str.strip()
                        return df
                except Exception:
                    continue
        st.error("Não foi possível parsear o CSV.")
        return None
    except Exception as e:
        st.error(f"Erro ao baixar: {e}")
        return None


def api_get(endpoint: str, params: dict = None) -> dict:
    try:
        r = requests.get(
            f"{API_BASE}{endpoint}",
            params=params,
            headers={"Accept": "application/json"},
            timeout=15,
        )
        st.caption(f"API {endpoint} → HTTP {r.status_code}")
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.error(f"Erro API: {e}")
    return {}


# ============================================================
# BLOCO 0 — BUSCAR ID DO DEPUTADO POR NOME
# ============================================================

st.header("0️⃣ Buscar ID do deputado por nome")

nome_dep = st.text_input("Nome (parcial)", placeholder="ex: Erika Kokay")
if st.button("Buscar deputado", key="btn_dep") and nome_dep:
    dados = api_get("/deputados", {
        "nome": nome_dep, "idLegislatura": 57, "itens": 10
    }).get("dados", [])
    if not dados:
        st.warning("Nenhum deputado encontrado.")
    else:
        rows = [{
            "id":      d.get("id"),
            "nome":    d.get("nome"),
            "partido": d.get("siglaPartido"),
            "uf":      d.get("siglaUf"),
        } for d in dados]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()


# ============================================================
# BLOCO 1 — COLUNAS DOS CSVs
# ============================================================

st.header("1️⃣ Colunas dos CSVs")

ano_col = st.selectbox("Ano", [2023, 2024, 2025], key="ano_col")

col1, col2 = st.columns(2)

with col1:
    st.subheader("votacoes-{ano}.csv")
    if st.button("Inspecionar", key="btn_vot"):
        with st.spinner("Baixando..."):
            df = baixar_csv(URL_VOTACOES.format(ano=ano_col))
        if df is not None:
            st.success(f"{len(df.columns)} colunas | {len(df):,} linhas")
            for i, c in enumerate(df.columns):
                st.text(f"[{i:02d}] {c}")
            st.dataframe(df.head(3), use_container_width=True)

with col2:
    st.subheader("votacoesVotos-{ano}.csv")
    if st.button("Inspecionar", key="btn_votos"):
        with st.spinner("Baixando (pode demorar ~1 min)..."):
            df = baixar_csv(URL_VOTOS.format(ano=ano_col), timeout=180)
        if df is not None:
            st.success(f"{len(df.columns)} colunas | {len(df):,} linhas")
            for i, c in enumerate(df.columns):
                st.text(f"[{i:02d}] {c}")
            st.dataframe(df.head(3), use_container_width=True)

st.divider()


# ============================================================
# BLOCO 2 — BUSCAR idVotacao DE UMA PROPOSIÇÃO
# ============================================================

st.header("2️⃣ Buscar idVotacao de uma proposição")
st.caption("Para os casos 'Não localizada' — descobre qual idVotacao usar como hardcoded.")

ALVOS_DEFAULT = [
    ("PL",  "1087", 2025, 2025, "Isenção IR R$5mil"),
    ("MPV", "1294", 2024, 2025, "MP da Taxação"),
    ("PL",  "1587", 2024, 2025, "Redução benefícios fiscais"),
    ("PL",  "2159", 2021, 2024, "Licenciamento ambiental"),
    ("PL",  "334",  2023, 2023, "Desoneração — derrubada veto"),
]

if st.button("🔍 Buscar todos os casos problemáticos", key="btn_alvos"):
    for sigla, numero, ano_prop, ano_vot, desc in ALVOS_DEFAULT:
        st.markdown(f"---\n**{desc} ({sigla} {numero}/{ano_prop} → votado em {ano_vot})**")
        dados_prop = api_get("/proposicoes", {
            "siglaTipo": sigla, "numero": numero, "ano": ano_prop
        }).get("dados", [])
        if not dados_prop:
            st.warning("Proposição não encontrada na API.")
            continue
        id_prop = dados_prop[0]["id"]
        st.write(f"✅ id_proposicao = `{id_prop}`")
        dados_vot = api_get("/votacoes", {
            "idProposicao": id_prop,
            "dataInicio": f"{ano_vot}-01-01",
            "dataFim":    f"{ano_vot}-12-31",
            "ordenarPor": "dataHoraRegistro",
            "ordem": "DESC", "itens": 10,
        }).get("dados", [])
        if not dados_vot:
            st.warning(f"Nenhuma votação encontrada via API em {ano_vot}.")
        else:
            rows = [{
                "idVotacao": v.get("id"),
                "data":      str(v.get("dataHoraRegistro", ""))[:10],
                "descricao": str(v.get("descricao", ""))[:100],
                "aprovacao": v.get("aprovacao"),
            } for v in dados_vot]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.code(f'"id_votacao": "{dados_vot[0]["id"]}"   # {desc}')

st.divider()


# ============================================================
# BLOCO 3 — BUSCA POR KEYWORD NA DESCRIÇÃO DO CSV
# ============================================================

st.header("3️⃣ Busca por keyword no CSV de votações")
st.caption(
    "Busca em TODAS as colunas de texto: descricao, ultimaApresentacaoProposicao_descricao "
    "e ultimaApresentacaoProposicao_uriProposicao. Quanto mais específica a keyword, melhor."
)

col_k1, col_k2, col_k3 = st.columns(3)
with col_k1:
    keyword = st.text_input("Palavra-chave", placeholder="ex: 1087  ou  isenção  ou  1294")
with col_k2:
    ano_kw = st.selectbox("Ano", [2023, 2024, 2025], key="ano_kw")
with col_k3:
    apenas_plenario = st.checkbox("Apenas PLEN (plenário)", value=True)

if st.button("Buscar", key="btn_kw") and keyword:
    with st.spinner("Baixando CSV de votações..."):
        df_vot = baixar_csv(URL_VOTACOES.format(ano=ano_kw))
    if df_vot is not None:
        colunas_texto = [c for c in df_vot.columns if any(
            t in c.lower() for t in ["descricao", "uri"]
        )]
        st.caption(f"Buscando nas colunas: {colunas_texto}")

        mask = pd.Series([False] * len(df_vot), index=df_vot.index)
        for col in colunas_texto:
            mask |= df_vot[col].astype(str).str.contains(keyword, case=False, na=False)

        if apenas_plenario and "siglaOrgao" in df_vot.columns:
            mask &= df_vot["siglaOrgao"].astype(str).str.upper() == "PLEN"

        resultado = df_vot[mask].copy()
        st.write(f"Matches: **{len(resultado)}**")
        if resultado.empty:
            st.warning("Nenhuma linha encontrada.")
            if "siglaOrgao" in df_vot.columns:
                st.write("Órgãos disponíveis:", df_vot["siglaOrgao"].value_counts().head(10).to_dict())
        else:
            st.success(f"{len(resultado)} votação(ões) encontrada(s)!")
            cols_show = [c for c in [
                "id", "data", "siglaOrgao", "aprovacao", "votosSimm", "votosNao",
                "descricao",
                "ultimaApresentacaoProposicao_descricao",
                "ultimaApresentacaoProposicao_idProposicao",
                "ultimaApresentacaoProposicao_uriProposicao",
            ] if c in df_vot.columns]
            st.dataframe(resultado[cols_show], use_container_width=True, hide_index=True)
            csv_out = resultado[cols_show].to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Exportar resultado", csv_out, "resultado_busca.csv", "text/csv")

st.divider()


# ============================================================
# BLOCO 4 — CRUZAMENTO POR idProposicao
# ============================================================

st.header("4️⃣ Cruzamento por idProposicao no CSV")
st.caption("Verifica se um idProposicao existe no campo ultimaApresentacaoProposicao_idProposicao.")

col_a, col_b = st.columns(2)
with col_a:
    id_prop_manual = st.text_input("idProposicao", placeholder="ex: 2487436")
with col_b:
    ano_cruz = st.selectbox("Ano do CSV", [2023, 2024, 2025], key="ano_cruz")

if st.button("Cruzar", key="btn_cruz") and id_prop_manual:
    with st.spinner("Baixando CSV de votações..."):
        df_vot = baixar_csv(URL_VOTACOES.format(ano=ano_cruz))
    if df_vot is not None:
        col_prop = next(
            (c for c in df_vot.columns if "idProposicao" in c),
            None,
        )
        if not col_prop:
            st.error(f"Coluna idProposicao não encontrada. Colunas: {df_vot.columns.tolist()}")
        else:
            mask = df_vot[col_prop].astype(str).str.strip() == str(id_prop_manual).strip()
            resultado = df_vot[mask]
            st.write(f"Coluna: `{col_prop}` | Matches: **{len(resultado)}**")
            if resultado.empty:
                st.warning("Nenhuma linha encontrada.")
                st.write("Exemplos de valores nessa coluna:")
                st.write(df_vot[col_prop].dropna().unique()[:10].tolist())
            else:
                st.success(f"{len(resultado)} linha(s) encontrada(s)!")
                st.dataframe(resultado, use_container_width=True, hide_index=True)

st.divider()


# ============================================================
# BLOCO 5 — VERIFICAR VOTO DE UM DEPUTADO
# ============================================================

st.header("5️⃣ Verificar voto de um deputado em uma votação")

col_c, col_d, col_e = st.columns(3)
with col_c:
    id_dep_manual = st.text_input("ID do Deputado", placeholder="ex: 204554")
with col_d:
    id_vot_manual = st.text_input("idVotacao", placeholder="ex: 2396574-68")
with col_e:
    ano_voto = st.selectbox("Ano", [2023, 2024, 2025], key="ano_voto")

if st.button("Buscar voto", key="btn_voto") and id_dep_manual and id_vot_manual:
    with st.spinner("Baixando CSV de votos (pode demorar)..."):
        df_votos = baixar_csv(URL_VOTOS.format(ano=ano_voto), timeout=180)
    if df_votos is not None:
        col_iv = next((c for c in df_votos.columns if "idVotacao" in c), None)
        col_id = next((c for c in df_votos.columns if "deputado_id" in c), None)
        col_v  = next((c for c in df_votos.columns if c in ("voto", "tipoVoto")), None)
        st.caption(f"Colunas → votacao={col_iv} | deputado={col_id} | voto={col_v}")

        if col_iv and col_id:
            linha = df_votos[
                (df_votos[col_iv].astype(str).str.strip() == str(id_vot_manual).strip()) &
                (df_votos[col_id].astype(str).str.strip() == str(id_dep_manual).strip())
            ]
            linhas_vot = df_votos[df_votos[col_iv].astype(str).str.strip() == str(id_vot_manual).strip()]
            st.write(f"Total de votos para esse idVotacao: **{len(linhas_vot)}**")
            if linha.empty:
                st.warning("Deputado não encontrado nessa votação — pode ser Ausente.")
                if not linhas_vot.empty:
                    st.write("Amostra de quem votou nessa votação:")
                    st.dataframe(linhas_vot.head(5), use_container_width=True, hide_index=True)
            else:
                st.success("Voto encontrado!")
                st.dataframe(linha, use_container_width=True, hide_index=True)
