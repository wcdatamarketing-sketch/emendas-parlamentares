# ============================================================
# utils/votacoes_relevantes.py
#
# Lista curada das principais votações do plenário da Câmara
# na 57ª legislatura (2023-2026) com repercussão nacional.
#
# Estratégia de cruzamento (nível 0 + 3 dinâmicos):
#
#   Nível 0 — id_votacao fixado na lista curada:
#     Para casos onde a busca dinâmica não resolve (MPV, vetos,
#     substitutivos). Obtenha via:
#     /api/v2/votacoes?idProposicao={id}
#
#   Nível 1 — idProposicao no CSV votacoes-{ano}.csv:
#     Campo ultimaApresentacaoProposicao_idProposicao.
#
#   Nível 2 — keyword regex na coluna descricao do CSV:
#     Padrão "SIGLA NUM" — cobre substitutivos e PECs.
#
#   Nível 3 — API /votacoes?idProposicao=...:
#     Fallback via API quando os CSVs não resolvem.
# ============================================================

VOTACOES_RELEVANTES = [
    # --- 2023 ---
    {
        "tema":      "Arcabouço fiscal (novo regime fiscal)",
        "sigla":     "PLP",
        "numero":    "93",
        "ano_prop":  2023,
        "ano_vot":   2023,
        "resultado": "Lei Complementar 200/23",
        "status":    "✅",
    },
    {
        "tema":      "Reforma tributária — PEC (IVA dual)",
        "sigla":     "PEC",
        "numero":    "45",
        "ano_prop":  2019,
        "ano_vot":   2023,
        "resultado": "EC 132/23 promulgada",
        "status":    "✅",
    },
    {
        "tema":      "Marco temporal das terras indígenas",
        "sigla":     "PL",
        "numero":    "490",
        "ano_prop":  2007,
        "ano_vot":   2023,
        "resultado": "Lei 14.701/23",
        "status":    "✅",
    },
    {
        "tema":      "Voto de qualidade no Carf (desempate pró-Fazenda)",
        "sigla":     "PL",
        "numero":    "2384",
        "ano_prop":  2023,
        "ano_vot":   2023,
        "resultado": "Lei 14.689/23",
        "status":    "✅",
    },
    {
        "tema":      "Apostas esportivas online (bets)",
        "sigla":     "PL",
        "numero":    "3626",
        "ano_prop":  2023,
        "ano_vot":   2023,
        "resultado": "Lei sancionada",
        "status":    "✅",
    },
    {
        "tema":      "Desoneração da folha — derrubada de veto presidencial",
        "sigla":     "PL",
        "numero":    "334",
        "ano_prop":  2023,
        "ano_vot":   2023,
        "resultado": "Veto de Lula derrubado",
        "status":    "✅",
        # Nota: derrubada de veto é registrada como MSC (Mensagem do Congresso),
        # não como PL. Resultado exibido como "Não localizada" até
        # o idVotacao do MSC ser identificado manualmente.
    },
    # --- 2024 ---
    {
        "tema":      "Regulamentação reforma tributária — 1ª fase (CBS/IBS)",
        "sigla":     "PLP",
        "numero":    "68",
        "ano_prop":  2024,
        "ano_vot":   2024,
        "resultado": "Lei Complementar sancionada",
        "status":    "✅",
    },
    {
        "tema":      "Desoneração da folha — reoneração gradual",
        "sigla":     "PL",
        "numero":    "1847",
        "ano_prop":  2024,
        "ano_vot":   2024,
        "resultado": "Lei — transição até 2027",
        "status":    "✅",
    },
    {
        "tema":      "Licenciamento ambiental — novo marco",
        "sigla":     "PL",
        "numero":    "2159",
        "ano_prop":  2021,
        "ano_vot":   2024,
        "resultado": "Lei sancionada",
        "status":    "✅",
        # Nota: proposição antiga — o texto votado foi um substitutivo
        # com ID diferente. "Não localizada" até confirmação do ID.
    },
    # --- 2025 ---
    {
        "tema":      "PEC das Prerrogativas (STF x Congresso)",
        "sigla":     "PEC",
        "numero":    "8",
        "ano_prop":  2021,
        "ano_vot":   2025,
        "resultado": "Aguarda Senado",
        "status":    "🔄",
    },
    {
        "tema":      "Isenção IR para renda até R$ 5 mil",
        "sigla":     "PL",
        "numero":    "1087",
        "ano_prop":  2025,
        "ano_vot":   2025,
        "resultado": "Lei 15.270/25 — vigor 2026",
        "status":    "✅",
    },
    {
        "tema":      "MP da Taxação — compensação fiscal do IR",
        "sigla":     "MPV",
        "numero":    "1294",
        "ano_prop":  2024,
        "ano_vot":   2025,
        "resultado": "Rejeitada — 251 x 193",
        "status":    "❌",
        # Nota: MPVs são votadas como PLV (substitutivo).
        # "Não localizada" até o idVotacao do PLV ser confirmado.
    },
    {
        "tema":      "Regulamentação reforma tributária — 2ª fase (Comitê IBS)",
        "sigla":     "PLP",
        "numero":    "108",
        "ano_prop":  2024,
        "ano_vot":   2025,
        "resultado": "Aprovada e sancionada",
        "status":    "✅",
    },
    {
        "tema":      "ECA Digital — crianças em ambiente digital",
        "sigla":     "PL",
        "numero":    "2628",
        "ano_prop":  2022,
        "ano_vot":   2025,
        "resultado": "Lei sancionada",
        "status":    "✅",
    },
    {
        "tema":      "PL Dosimetria — penas dos condenados do 8 de Janeiro",
        "sigla":     "PL",
        "numero":    "2858",
        "ano_prop":  2022,
        "ano_vot":   2025,
        "resultado": "No Senado (291 x 148)",
        "status":    "🔄",
    },
    {
        "tema":      "Redução de benefícios fiscais + taxação bets e fintechs",
        "sigla":     "PL",
        "numero":    "1587",
        "ano_prop":  2024,
        "ano_vot":   2025,
        "resultado": "Aprovado",
        "status":    "✅",
        # Nota: votado como substitutivo — id_votacao a confirmar.
    },
    # --- 2026 (em andamento) ---
    {
        "tema":      "Fim da escala 6×1 — PEC 8/25",
        "sigla":     "PEC",
        "numero":    "8",
        "ano_prop":  2025,
        "ano_vot":   2026,
        "resultado": "Comissão especial — votação iminente",
        "status":    "🔄",
    },
    {
        "tema":      "Regulação de IA e big techs",
        "sigla":     "PL",
        "numero":    "2338",
        "ano_prop":  2023,
        "ano_vot":   2026,
        "resultado": "Em discussão",
        "status":    "🔄",
    },
    {
        "tema":      "Trabalho por aplicativos (regulamentação)",
        "sigla":     "PL",
        "numero":    "3337",
        "ano_prop":  2024,
        "ano_vot":   2026,
        "resultado": "Prioridade 2026",
        "status":    "🔄",
    },
    {
        "tema":      "PEC Segurança Pública (cooperação União–estados)",
        "sigla":     "PEC",
        "numero":    "14",
        "ano_prop":  2021,
        "ano_vot":   2026,
        "resultado": "Comissão especial",
        "status":    "🔄",
    },
    {
        "tema":      "Lei Antifacção (crime organizado)",
        "sigla":     "PL",
        "numero":    "2785",
        "ano_prop":  2022,
        "ano_vot":   2026,
        "resultado": "Câmara analisa substitutivo",
        "status":    "🔄",
    },
    {
        "tema":      "Acordo Mercosul–União Europeia (ratificação)",
        "sigla":     "MSC",
        "numero":    "572",
        "ano_prop":  2023,
        "ano_vot":   2026,
        "resultado": "Comissão mista",
        "status":    "🔄",
    },
]


# ============================================================
# IMPORTS
# ============================================================

import io
import re
import requests
import pandas as pd
import streamlit as st

URL_VOTACOES_CSV = (
    "https://dadosabertos.camara.leg.br/arquivos/votacoes"
    "/csv/votacoes-{ano}.csv"
)
URL_VOTOS_CSV = (
    "https://dadosabertos.camara.leg.br/arquivos/votacoesVotos"
    "/csv/votacoesVotos-{ano}.csv"
)


# ============================================================
# DOWNLOAD E CACHE DOS CSVs
# ============================================================

@st.cache_data(ttl=86400, show_spinner=False)
def _baixar_votacoes_ano(ano: int) -> pd.DataFrame | None:
    """Baixa e cacheia o CSV de votações de um ano."""
    try:
        resp = requests.get(URL_VOTACOES_CSV.format(ano=ano), timeout=60)
        resp.raise_for_status()
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
    except Exception:
        return None
    return None


@st.cache_data(ttl=86400, show_spinner=False)
def _baixar_votos_ano(ano: int) -> pd.DataFrame | None:
    """Baixa e cacheia o CSV de votos de um ano."""
    try:
        resp = requests.get(URL_VOTOS_CSV.format(ano=ano), timeout=180)
        resp.raise_for_status()
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
    except Exception:
        return None
    return None


# ============================================================
# HELPERS
# ============================================================

def _detectar_coluna(df: pd.DataFrame, candidatos: list) -> str | None:
    """Retorna o primeiro nome de coluna que existir no DataFrame."""
    for c in candidatos:
        if c in df.columns:
            return c
    return None


@st.cache_data(ttl=86400, show_spinner=False)
def _buscar_id_proposicao(sigla: str, numero: str, ano_prop: int) -> str | None:
    """Busca o ID da proposição na API da Câmara."""
    try:
        r = requests.get(
            "https://dadosabertos.camara.leg.br/api/v2/proposicoes",
            params={"siglaTipo": sigla, "numero": numero, "ano": ano_prop},
            headers={"Accept": "application/json"},
            timeout=10,
        )
        dados = r.json().get("dados", [])
        if dados:
            return str(dados[0].get("id", ""))
    except Exception:
        pass
    return None


# ============================================================
# BUSCA DO idVotacao — NÍVEL 0 + 3 DINÂMICOS
# ============================================================

def _selecionar_votacao_principal(df: pd.DataFrame, col_id: str) -> str | None:
    """
    Seleciona a votação principal dentre candidatas.

    A votação nominal (texto principal) sempre tem mais votos que
    procedimentos (requerimentos, encaminhamentos, redação final).
    Ordena por votosSimm + votosNao decrescente e pega o topo.
    Fallback: último sequencial.
    """
    if df.empty:
        return None

    col_sim = _detectar_coluna(df, ["votosSimm", "votosSim"])
    col_nao = _detectar_coluna(df, ["votosNao"])

    if col_sim and col_nao:
        try:
            df = df.copy()
            df["_total"] = (
                pd.to_numeric(df[col_sim], errors="coerce").fillna(0) +
                pd.to_numeric(df[col_nao], errors="coerce").fillna(0)
            )
            df_sorted = df.sort_values("_total", ascending=False)
            if df_sorted.iloc[0]["_total"] > 0:
                return str(df_sorted.iloc[0][col_id]).strip()
        except Exception:
            pass

    # Fallback: último sequencial
    return str(df.iloc[-1][col_id]).strip()


@st.cache_data(ttl=86400, show_spinner=False)
def buscar_id_votacao(
    sigla: str,
    numero: str,
    ano_prop: int,
    ano_vot: int,
    id_votacao_fixo: str = None,
) -> str | None:
    """
    Localiza o idVotacao da votação PRINCIPAL de uma proposição.

    Nível 0: usa id_votacao_fixo se informado (hardcoded).
    Nível 1: cruza por idProposicao no CSV + seleciona votação principal.
    Nível 2: cruza por URI da proposição no CSV + seleciona votação principal.
    Nível 3: regex SIGLA+NUM na descricao + seleciona votação principal.
    Nível 4: API /votacoes?idProposicao=... (fallback remoto).
    """
    # --- Nível 0 ---
    if id_votacao_fixo:
        return str(id_votacao_fixo).strip()

    id_prop = _buscar_id_proposicao(sigla, numero, ano_prop)
    df_vot  = _baixar_votacoes_ano(ano_vot)

    if df_vot is None:
        return None

    col_id_vot  = _detectar_coluna(df_vot, ["id", "idVotacao"])
    col_prop_id = _detectar_coluna(df_vot, ["ultimaApresentacaoProposicao_idProposicao"])
    col_prop_uri= _detectar_coluna(df_vot, ["ultimaApresentacaoProposicao_uriProposicao"])
    col_descr   = _detectar_coluna(df_vot, ["descricao"])

    if not col_id_vot:
        return None

    # --- Nível 1 — idProposicao no campo idProposicao ---
    if id_prop and col_prop_id:
        mask = df_vot[col_prop_id].astype(str).str.strip() == str(id_prop).strip()
        resultado = df_vot[mask]
        if not resultado.empty and col_descr:
            id_vot = _selecionar_votacao_principal(resultado, col_id_vot)
            if id_vot:
                return id_vot

    # --- Nível 2 — idProposicao na URI ---
    if id_prop and col_prop_uri:
        mask = df_vot[col_prop_uri].astype(str).str.contains(
            str(id_prop), regex=False, na=False
        )
        resultado = df_vot[mask]
        if not resultado.empty and col_descr:
            id_vot = _selecionar_votacao_principal(resultado, col_id_vot)
            if id_vot:
                return id_vot

    # --- Nível 3 — regex SIGLA+NUM na descricao ---
    if col_descr:
        padrao = rf"(?i){re.escape(sigla)}\s*[./-]?\s*{re.escape(numero)}"
        mask = df_vot[col_descr].astype(str).str.contains(padrao, regex=True, na=False)
        resultado = df_vot[mask]
        if not resultado.empty:
            id_vot = _selecionar_votacao_principal(resultado, col_id_vot)
            if id_vot:
                return id_vot

    # --- Nível 4 — API /votacoes (fallback remoto) ---
    if id_prop:
        try:
            r = requests.get(
                "https://dadosabertos.camara.leg.br/api/v2/votacoes",
                params={
                    "idProposicao": id_prop,
                    "dataInicio":   f"{ano_vot}-01-01",
                    "dataFim":      f"{ano_vot}-12-31",
                    "ordenarPor":   "dataHoraRegistro",
                    "ordem":        "DESC",
                    "itens":        10,
                },
                headers={"Accept": "application/json"},
                timeout=10,
            )
            dados = r.json().get("dados", [])
            if dados:
                id_vot = str(dados[0].get("id", ""))
                if id_vot:
                    return id_vot
        except Exception:
            pass

    return None


# ============================================================
# VOTO DO DEPUTADO EM UMA VOTAÇÃO ESPECÍFICA
# ============================================================

def buscar_voto_deputado(id_deputado: int, id_votacao: str, ano_vot: int) -> str:
    """
    Retorna o voto formatado de um deputado em uma votação.
    Cruza votacoesVotos-{ano}.csv por idVotacao + deputado_id.
    """
    df_votos = _baixar_votos_ano(ano_vot)
    if df_votos is None:
        return "—"

    col_id_vot = _detectar_coluna(df_votos, ["idVotacao"])
    col_id_dep = _detectar_coluna(df_votos, ["deputado_id", "idDeputado"])
    col_voto   = _detectar_coluna(df_votos, ["voto", "tipoVoto"])

    if not col_id_vot or not col_id_dep or not col_voto:
        return "—"

    linha = df_votos[
        (df_votos[col_id_vot].astype(str).str.strip() == str(id_votacao).strip()) &
        (df_votos[col_id_dep].astype(str).str.strip() == str(id_deputado).strip())
    ]

    if linha.empty:
        return "Ausente"

    voto_raw = linha.iloc[0][col_voto].strip().upper()

    mapa = {
        "SIM":       "✅ Sim",
        "NÃO":       "❌ Não",
        "NAO":       "❌ Não",
        "ABSTENÇÃO": "➖ Abstenção",
        "ABSTENCAO": "➖ Abstenção",
        "OBSTRUÇÃO": "🚫 Obstrução",
        "OBSTRUCAO": "🚫 Obstrução",
        "ART. 17":   "📋 Art. 17",
    }
    return mapa.get(voto_raw, voto_raw.title())


# ============================================================
# ENTRY POINT PRINCIPAL
# ============================================================

@st.cache_data(ttl=3600, show_spinner="Buscando votações relevantes...")
def buscar_votos_relevantes_deputado(id_deputado: int) -> list:
    """
    Retorna os votos de um deputado nas votações relevantes curadas.
    """
    resultados = []

    for v in VOTACOES_RELEVANTES:
        # Votações ainda não realizadas
        if v["status"] == "🔄":
            resultados.append({
                "tema":      v["tema"],
                "status":    v["status"],
                "resultado": v["resultado"],
                "voto":      "🔄 Ainda não votada",
                "ano":       v["ano_vot"],
            })
            continue

        id_vot = buscar_id_votacao(
            sigla           = v["sigla"],
            numero          = v["numero"],
            ano_prop        = v["ano_prop"],
            ano_vot         = v["ano_vot"],
            id_votacao_fixo = v.get("id_votacao"),  # Nível 0 se definido
        )

        voto = (
            buscar_voto_deputado(id_deputado, id_vot, v["ano_vot"])
            if id_vot
            else "⚠️ Não localizada"
        )

        resultados.append({
            "tema":      v["tema"],
            "status":    v["status"],
            "resultado": v["resultado"],
            "voto":      voto,
            "ano":       v["ano_vot"],
        })

    return resultados
