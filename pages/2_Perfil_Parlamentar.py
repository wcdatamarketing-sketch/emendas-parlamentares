# ============================================================
# pages/2_Perfil_Parlamentar.py
# Tela de perfil completo de um parlamentar —
# exibe emendas, distribuição por área, execução e projetos
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px

# Importamos as funções de cache para buscar os dados
from utils.cache import (
    cache_emendas_por_autor,
    cache_deputado_por_nome,
    cache_proposicoes_do_deputado,
)

# Importamos os formatadores
from utils.formatters import (
    formatar_moeda,
    formatar_moeda_resumida,
    calcular_percentual_execucao,
    formatar_data,
    limpar_nome,
    valor_ou_traco,
)


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Perfil do Parlamentar — Emendas",
    page_icon="👤",
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
    "<h1 style='color:#1a3a5c;'>👤 Perfil do Parlamentar</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "Busque um parlamentar para ver suas emendas, "
    "distribuição por área temática e projetos legislativos."
)
st.divider()


# ============================================================
# CAMPO DE BUSCA
# ============================================================

# Divide em duas colunas — busca à esquerda, ano à direita
col_busca, col_ano = st.columns([3, 1])

with col_busca:
    # text_input para digitar o nome do parlamentar
    nome_buscado = st.text_input(
        "Nome do parlamentar",
        placeholder="Digite o nome do deputado ou senador...",
    )

with col_ano:
    ano = st.selectbox(
        "Ano de referência",
        options=[2024, 2023, 2022],
    )

# Só executa o restante se o usuário digitou algo
# "not nome_buscado" é True quando o campo está vazio
if not nome_buscado:
    st.info("👆 Digite o nome de um parlamentar para começar.")
    st.stop()


# ============================================================
# BUSCA DOS DADOS DE EMENDAS
# ============================================================

with st.spinner(f"Buscando emendas de {nome_buscado}..."):
    emendas_raw = cache_emendas_por_autor(api_key, nome_buscado, ano)

if not emendas_raw:
    st.warning(
        f"Nenhuma emenda encontrada para '{nome_buscado}' em {ano}. "
        "Verifique o nome e tente novamente."
    )
    st.stop()

# Converte para DataFrame
df = pd.DataFrame(emendas_raw)

# Garante que as colunas de valor são numéricas
for coluna in ["valorEmpenhado", "valorPago", "valorLiquidado"]:
    if coluna in df.columns:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0)


# ============================================================
# CABEÇALHO DO PARLAMENTAR
# ============================================================

# Pega informações básicas do parlamentar da primeira emenda
# (todos os registros têm o mesmo autor, então pegamos o primeiro)
nome_autor = limpar_nome(df["nomeAutor"].iloc[0] if "nomeAutor" in df.columns else nome_buscado)
# iloc[0] acessa a primeira linha do DataFrame pelo índice numérico

partido = df["partidoAutor"].iloc[0] if "partidoAutor" in df.columns else "—"
uf = df["ufAutor"].iloc[0] if "ufAutor" in df.columns else "—"
tipo = df["tipoAutor"].iloc[0] if "tipoAutor" in df.columns else "—"

# Exibe o cabeçalho com os dados do parlamentar
st.markdown(f"""
    <div style='background:#f0f4f8; padding:1.5rem; border-radius:10px;
                border-left:5px solid #1a3a5c; margin-bottom:1rem;'>
        <h2 style='color:#1a3a5c; margin:0;'>{nome_autor}</h2>
        <p style='color:#555; margin:0.3rem 0 0 0; font-size:1.1rem;'>
            {partido} &nbsp;|&nbsp; {uf} &nbsp;|&nbsp; {tipo}
        </p>
    </div>
""", unsafe_allow_html=True)


# ============================================================
# CARDS DE RESUMO
# ============================================================

st.markdown("### 📈 Resumo das emendas")

c1, c2, c3, c4 = st.columns(4)

total_empenhado = df["valorEmpenhado"].sum()
total_pago = df["valorPago"].sum() if "valorPago" in df.columns else 0
total_emendas = len(df)

with c1:
    st.metric("Total de emendas", total_emendas)

with c2:
    st.metric("Total empenhado", formatar_moeda_resumida(total_empenhado))

with c3:
    st.metric("Total pago", formatar_moeda_resumida(total_pago))

with c4:
    st.metric(
        "Taxa de execução",
        calcular_percentual_execucao(total_empenhado, total_pago)
    )

st.divider()


# ============================================================
# GRÁFICOS — DISTRIBUIÇÃO
# ============================================================

# Divide em duas colunas para os dois gráficos ficarem lado a lado
col_area, col_uf = st.columns(2)

with col_area:
    st.markdown("#### 🎯 Distribuição por área temática")

    # Verifica se a coluna de função existe no DataFrame
    if "funcao" in df.columns:

        # Agrupa e soma por área temática
        por_area = df.groupby("funcao")["valorEmpenhado"].sum().reset_index()
        por_area.columns = ["Área", "Valor"]

        # Ordena do maior para o menor
        por_area = por_area.sort_values("Valor", ascending=False)

        # Gráfico de pizza (pie chart)
        fig_area = px.pie(
            por_area,
            names="Área",       # coluna com os rótulos
            values="Valor",     # coluna com os valores
            hole=0.4,           # furo no centro — vira um gráfico "donut"
            color_discrete_sequence=px.colors.sequential.Blues_r,
            # Blues_r = paleta de azuis do claro ao escuro
        )
        fig_area.update_layout(
            showlegend=True,
            height=350,
            margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig_area, use_container_width=True)

    else:
        st.info("Dados de área temática não disponíveis.")

with col_uf:
    st.markdown("#### 🗺️ Distribuição por estado beneficiado")

    # Verifica se a coluna de UF do favorecido existe
    if "ufFavorecido" in df.columns:

        por_uf = df.groupby("ufFavorecido")["valorEmpenhado"].sum().reset_index()
        por_uf.columns = ["UF", "Valor"]
        por_uf = por_uf.sort_values("Valor", ascending=False).head(10)
        # head(10) pega apenas os 10 primeiros — evita gráfico poluído

        fig_uf = px.bar(
            por_uf,
            x="UF",
            y="Valor",
            color="Valor",
            # color com valor numérico cria gradiente de cor automático
            color_continuous_scale="Blues",
            labels={"Valor": "Total Empenhado (R$)", "UF": "Estado"},
        )
        fig_uf.update_layout(
            height=350,
            showlegend=False,
            plot_bgcolor="white",
            coloraxis_showscale=False,  # esconde a barra de escala de cor
            margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig_uf, use_container_width=True)

    else:
        st.info("Dados de UF do favorecido não disponíveis.")

st.divider()


# ============================================================
# TABELA DE EMENDAS
# ============================================================

st.markdown("### 📋 Lista de emendas")

# Monta a tabela apenas com as colunas que existem no DataFrame
# isso evita erros caso a API não retorne alguma coluna
colunas_disponiveis = {
    "numeroEmenda": "Nº Emenda",
    "tipoEmenda": "Tipo",
    "funcao": "Área Temática",
    "nomeFavorecido": "Favorecido",
    "ufFavorecido": "UF",
    "municipioFavorecido": "Município",
    "valorEmpenhado": "Empenhado",
    "valorPago": "Pago",
}

# Filtra apenas as colunas que existem no DataFrame retornado pela API
colunas_existentes = {
    k: v for k, v in colunas_disponiveis.items() if k in df.columns
}
# Essa linha usa "dict comprehension" — cria um dicionário novo
# incluindo apenas os pares onde a chave (k) existe no DataFrame

# Cria DataFrame apenas com as colunas disponíveis
tabela = df[list(colunas_existentes.keys())].copy()

# Renomeia as colunas para os nomes amigáveis
tabela.columns = list(colunas_existentes.values())

# Formata os valores monetários se as colunas existirem
if "Empenhado" in tabela.columns:
    tabela["Empenhado"] = tabela["Empenhado"].apply(formatar_moeda)
if "Pago" in tabela.columns:
    tabela["Pago"] = tabela["Pago"].apply(formatar_moeda)

st.dataframe(
    tabela,
    use_container_width=True,
    hide_index=True,
    height=400,
)

# Botão para baixar CSV
csv = df.to_csv(index=False, encoding="utf-8-sig")
st.download_button(
    label="⬇️ Baixar dados em CSV",
    data=csv,
    file_name=f"emendas_{nome_buscado.replace(' ', '_')}_{ano}.csv",
    mime="text/csv",
)

st.divider()


# ============================================================
# PROJETOS LEGISLATIVOS (API DA CÂMARA)
# ============================================================

st.markdown("### 🏛️ Projetos legislativos apresentados")
st.caption(
    "Dados disponíveis apenas para Deputados Federais — "
    "integração com a API de Dados Abertos da Câmara dos Deputados."
)

# Busca o deputado pelo nome para obter o ID
with st.spinner("Buscando projetos legislativos..."):
    deputados_encontrados = cache_deputado_por_nome(nome_buscado)

# Se não encontrou nenhum deputado com esse nome
if not deputados_encontrados:
    st.info(
        "Nenhum deputado federal encontrado com esse nome. "
        "Para senadores, os projetos legislativos estarão disponíveis em breve."
    )
else:
    # Se encontrou mais de um, deixa o usuário escolher
    if len(deputados_encontrados) > 1:

        # Cria lista de opções com nome e partido para facilitar a escolha
        opcoes = [
            f"{d.get('nome', '')} ({d.get('siglaPartido', '')} - {d.get('siglaUf', '')})"
            for d in deputados_encontrados
        ]

        escolha = st.selectbox(
            "Mais de um deputado encontrado — selecione o correto:",
            options=opcoes,
        )

        # Pega o índice da opção escolhida para acessar o deputado correto
        indice_escolhido = opcoes.index(escolha)
        deputado = deputados_encontrados[indice_escolhido]

    else:
        # Se encontrou apenas um, usa direto
        deputado = deputados_encontrados[0]

    # Pega o ID do deputado — necessário para buscar as proposições
    id_deputado = deputado.get("id")

    if id_deputado:
        with st.spinner("Carregando projetos..."):
            proposicoes = cache_proposicoes_do_deputado(id_deputado, ano)

        if not proposicoes:
            st.info(f"Nenhum projeto encontrado para {ano}.")
        else:
            st.success(f"{len(proposicoes)} projetos encontrados em {ano}.")

            # Monta tabela de proposições
            tabela_proj = pd.DataFrame(proposicoes)

            # Seleciona e renomeia colunas disponíveis
            colunas_proj = {
                "siglaTipo": "Tipo",
                "numero": "Número",
                "ano": "Ano",
                "ementa": "Ementa",
                "dataApresentacao": "Data",
            }

            colunas_proj_existentes = {
                k: v for k, v in colunas_proj.items()
                if k in tabela_proj.columns
            }

            tabela_proj = tabela_proj[list(colunas_proj_existentes.keys())].copy()
            tabela_proj.columns = list(colunas_proj_existentes.values())

            # Formata a data se existir
            if "Data" in tabela_proj.columns:
                tabela_proj["Data"] = tabela_proj["Data"].apply(formatar_data)

            st.dataframe(
                tabela_proj,
                use_container_width=True,
                hide_index=True,
                height=400,
            )
