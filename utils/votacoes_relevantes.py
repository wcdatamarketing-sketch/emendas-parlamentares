# ============================================================
# utils/votacoes_relevantes.py
#
# Lista curada das principais votações do plenário da Câmara
# na 57ª legislatura (2023-2026) com repercussão nacional.
#
# Estratégia de cruzamento:
#   1. CSVs anuais de votações: votacoes-{ano}.csv
#      Cada linha tem idVotacao + descrição
#   2. Busca por siglaTipo+número+ano da proposição
#   3. Cruza com votacoesVotos-{ano}.csv pelo idVotacao
#      para pegar o voto de cada deputado
#
# Os IDs são buscados dinamicamente — não hardcodados —
# para resistir a mudanças na API.
# ============================================================

# ============================================================
# LISTA CURADA DE VOTAÇÕES RELEVANTES
# Cada item tem:
#   tema:       descrição curta para exibição
#   sigla:      tipo da proposição (PEC, PLP, PL, etc.)
#   numero:     número da proposição
#   ano_prop:   ano de apresentação da proposição
#   ano_vot:    ano em que foi votada na Câmara
#   resultado:  resultado geral da votação
#   status:     ✅ Aprovada | ❌ Rejeitada | 🔄 Em andamento
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
        "tema":      "Desoneração da folha — derrubada de veto",
        "sigla":     "PL",
        "numero":    "334",
        "ano_prop":  2023,
        "ano_vot":   2023,
        "resultado": "Veto de Lula derrubado",
        "status":    "✅",
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
        "tema":      "MP da Taxação (compensação fiscal do IR) — derrubada",
        "sigla":     "MPV",
        "numero":    "1294",
        "ano_prop":  2024,
        "ano_vot":   2025,
        "resultado": "Rejeitada — 251 x 193",
        "status":    "❌",
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
# BUSCA DOS IDs DE VOTAÇÃO NOS CSVs ANUAIS
# ============================================================

import io
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


@st.cache_data(ttl=86400, show_spinner=False)
def _inspecionar_csv_votacoes(ano: int) -> dict:
    """Retorna metadados do CSV de votações para diagnóstico."""
    df = _baixar_votacoes_ano(ano)
    if df is None:
        return {"erro": "CSV não baixado"}
    return {
        "colunas": list(df.columns),
        "linhas": len(df),
        "amostra": df.iloc[0].to_dict() if len(df) > 0 else {},
    }


def buscar_id_votacao(sigla: str, numero: str, ano_prop: int, ano_vot: int) -> str | None:
    """
    Busca o idVotacao de uma proposição nos CSVs anuais.
    """
    df_vot = _baixar_votacoes_ano(ano_vot)
    if df_vot is None:
        return None

    # Log das colunas disponíveis (só na primeira vez por sessão)
    if "votacoes_cols_logadas" not in st.session_state:
        st.session_state["votacoes_cols_logadas"] = True
        st.info(f"📋 Colunas CSV votações {ano_vot}: {list(df_vot.columns)}")
        if len(df_vot) > 0:
            st.info(f"📄 Exemplo linha 1: {df_vot.iloc[0].to_dict()}")

    # Coluna de descrição da votação
    col_desc = next(
        (c for c in df_vot.columns if "descricao" in c.lower() or "objeto" in c.lower() or "proposicao" in c.lower()),
        None,
    )
    col_id = next(
        (c for c in df_vot.columns if c.lower() in ["id", "idvotacao", "id_votacao"]),
        None,
    )

    if not col_desc or not col_id:
        st.warning(f"⚠️ Colunas não encontradas: desc={col_desc} | id={col_id}")
        return None

    # Busca pela sigla e número na descrição
    mask = (
        df_vot[col_desc].str.contains(f"{sigla} {numero}", case=False, na=False, regex=False)
    )

    resultado = df_vot[mask]
    if resultado.empty:
        return None

    return resultado.iloc[0][col_id]


def buscar_voto_deputado(id_deputado: int, id_votacao: str, ano_vot: int) -> str:
    """
    Retorna o voto de um deputado em uma votação específica.

    id_deputado: ID do deputado na API da Câmara
    id_votacao:  ID da votação
    ano_vot:     ano em que ocorreu a votação

    Retorna: "Sim", "Não", "Abstenção", "Obstrução", "Ausente" ou "—"
    """
    df_votos = _baixar_votos_ano(ano_vot)
    if df_votos is None:
        return "—"

    col_id_vot = next(
        (c for c in df_votos.columns if "idvotacao" in c.lower() or c.lower() == "id_votacao"),
        None,
    )
    col_id_dep = next(
        (c for c in df_votos.columns if "iddeputado" in c.lower() or "id_deputado" in c.lower()),
        None,
    )
    col_voto = next(
        (c for c in df_votos.columns if c.lower() in ["tipovoto", "voto"]),
        None,
    )

    if not col_id_vot or not col_id_dep or not col_voto:
        return "—"

    linha = df_votos[
        (df_votos[col_id_vot].astype(str) == str(id_votacao)) &
        (df_votos[col_id_dep].astype(str) == str(id_deputado))
    ]

    if linha.empty:
        return "Ausente"

    voto_raw = linha.iloc[0][col_voto].strip().upper()

    mapa = {
        "SIM":        "✅ Sim",
        "NÃO":        "❌ Não",
        "NAO":        "❌ Não",
        "ABSTENÇÃO":  "➖ Abstenção",
        "ABSTENCAO":  "➖ Abstenção",
        "OBSTRUÇÃO":  "🚫 Obstrução",
        "OBSTRUCAO":  "🚫 Obstrução",
        "ART. 17":    "📋 Art. 17",
    }
    return mapa.get(voto_raw, voto_raw.title())


@st.cache_data(ttl=3600, show_spinner="Buscando votações relevantes...")
def buscar_votos_relevantes_deputado(id_deputado: int) -> list:
    """
    Retorna os votos de um deputado nas votações relevantes curadas.
    Só busca votações que já ocorreram (status ✅ ou ❌).

    Retorna lista de dicts:
    [
        {
            "tema": str,
            "status": str,
            "resultado": str,
            "voto": str,
            "ano": int,
        }
    ]
    """
    resultados = []

    for v in VOTACOES_RELEVANTES:
        # Pula votações ainda em andamento
        if v["status"] == "🔄":
            resultados.append({
                "tema":      v["tema"],
                "status":    v["status"],
                "resultado": v["resultado"],
                "voto":      "🔄 Ainda não votada",
                "ano":       v["ano_vot"],
            })
            continue

        # Busca o ID da votação
        id_vot = buscar_id_votacao(
            v["sigla"], v["numero"], v["ano_prop"], v["ano_vot"]
        )

        if id_vot:
            voto = buscar_voto_deputado(id_deputado, id_vot, v["ano_vot"])
        else:
            voto = "⚠️ Não localizada"

        resultados.append({
            "tema":      v["tema"],
            "status":    v["status"],
            "resultado": v["resultado"],
            "voto":      voto,
            "ano":       v["ano_vot"],
        })

    return resultados
