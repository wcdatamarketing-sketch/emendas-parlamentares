# ============================================================
# pages/1_Ranking.py
# Tela inicial do site — exibe o ranking geral de parlamentares
# ordenado por volume de emendas na legislatura atual
# ============================================================

# Importamos as bibliotecas necessárias para essa tela
import streamlit as st   # interface visual
import pandas as pd      # manipulação de tabelas
import plotly.express as px  # gráficos interativos

# Importamos as funções de cache que criamos em utils/cache.py
# essas funções buscam os dados já com cache automático de 1 hora
from utils.cache import cache_emendas_ranking

# Importamos os formatadores para exibir valores corretamente
from utils.formatters import (
    formatar_moeda,
    formatar_moeda_resumida,
    formatar_percentual,
    calcular_percentual_execucao,
    limpar_nome,
)


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Ranking — Emendas Parlamentares",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# VERIFICAÇÃO DA CHAVE DE API
# ============================================================

# Verifica se a chave existe no session_state
# (foi guardada lá pelo app.py quando o usuário entrou no site)
if "api_key" not in st.session_state:
    st.error("⚠️ Acesse a plataforma pela página inicial.")
    st.stop()

# Pega a chave do session_state para usar nas chamadas de API
api_key = st.session_state.api_key


# ============================================================
# CABEÇALHO DA TELA
# ============================================================

st.markdown(
    "<h1 style='color:#1a3a5c;'>📊 Ranking de Parlamentares</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "Parlamentares ordenados pelo total de emendas empenhadas. "
    "Use os filtros para refinar a busca."
)
st.divider()


# ============================================================
# FILTROS
# ============================================================

# Cria uma linha com 4 colunas para os filtros ficarem lado a lado
col_ano, col_tipo, col_partido, col_uf = st.columns(4)

with col_ano:
    # selectbox cria um menu suspenso de seleção
    # o primeiro argumento é o rótulo, o segundo é a lista de opções
    ano = st.selectbox(
        "Ano",
        options=[2024, 2023, 2022],  # anos disponíveis
        index=0,                      # índice 0 = primeiro item selecionado por padrão
    )

with col_tipo:
    tipo_autor = st.selectbox(
        "Tipo de parlamentar",
        options=["Todos", "Deputado Federal", "Senador"],
    )

with col_partido:
    # text_input cria um campo de texto livre para digitar
    partido = st.text_input(
        "Partido",
        placeholder="Ex: PT, PL, MDB...",  # texto de dica dentro do campo
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


# ============================================================
# BUSCA DOS DADOS
# ============================================================

# st.spinner exibe uma animação de carregamento enquanto
# os dados estão sendo buscados — melhora a experiência do usuário
with st.spinner("Buscando dados da API do Portal da Transparência..."):
    
    # Chama a função de cache que busca os dados
    # se já foram buscados na última hora, vem instantâneo
    emendas_raw = cache_emendas_ranking(api_key, ano)

# Se não retornou nenhum dado, exibe aviso e para a execução
if not emendas_raw:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()


# ============================================================
# PROCESSAMENTO DOS DADOS
# ============================================================

# Converte a lista de dicionários em um DataFrame do pandas
# DataFrame é como uma tabela Excel — tem linhas e colunas
# e permite filtrar, agrupar e calcular facilmente
df = pd.DataFrame(emendas_raw)

# Garante que as colunas de valor existem e são numéricas
# "get" é seguro — se a coluna não existir, usa 0 como padrão
# pd.to_numeric converte texto para número, erros viram 0
for coluna in ["valorEmpenhado", "valorPago", "valorLiquidado"]:
    if coluna in df.columns:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0)
        # errors="coerce": se não conseguir converter, coloca NaN
        # fillna(0): substitui NaN por 0


# ============================================================
# APLICAÇÃO DOS FILTROS
# ============================================================

# Filtra por tipo de autor se não for "Todos"
if tipo_autor != "Todos" and "tipoAutor" in df.columns:
    # str.contains verifica se a coluna contém o texto
    # case=False ignora maiúsculas/minúsculas
    # na=False trata valores nulos como False
    df = df[df["tipoAutor"].str.contains(tipo_autor, case=False, na=False)]

# Filtra por partido se foi digitado algum texto
if partido and "partidoAutor" in df.columns:
    df = df[df["partidoAutor"].str.contains(partido, case=False, na=False)]

# Filtra por UF se não for "Todos"
if uf != "Todos" and "ufAutor" in df.columns:
    df = df[df["ufAutor"] == uf]

# Se após os filtros não sobrou nada, avisa o usuário
if df.empty:
    st.warning("Nenhum parlamentar encontrado com os filtros aplicados.")
    st.stop()


# ============================================================
# AGRUPAMENTO POR PARLAMENTAR
# ============================================================

# groupby agrupa as linhas pelo nome do autor
# agg define o que calcular para cada coluna ao agrupar:
# - sum: soma todos os valores do grupo
# - first: pega o primeiro valor (para campos que se repetem)
ranking = df.groupby("nomeAutor").agg(
    total_empenhado=("valorEmpenhado", "sum"),
    total_pago=("valorPago", "sum"),
    quantidade_emendas=("valorEmpenhado", "count"),
    partido=("partidoAutor", "first"),
    uf=("ufAutor", "first"),
    tipo=("tipoAutor", "first"),
).reset_index()
# reset_index() transforma o índice de volta em coluna normal

# Ordena pelo total empenhado — do maior para o menor
ranking = ranking.sort_values("total_empenhado", ascending=False)

# Adiciona coluna de percentual de execução
ranking["execucao"] = ranking.apply(
    # apply executa uma função em cada linha do DataFrame
    # lambda é uma função anônima de uma linha
    # row é cada linha, acessamos as colunas pelo nome
    lambda row: calcular_percentual_execucao(
        row["total_empenhado"], row["total_pago"]
    ),
    axis=1,  # axis=1 significa "aplica por linha" (axis=0 seria por coluna)
)

# Adiciona posição no ranking (1º, 2º, 3º...)
ranking.insert(0, "posição", range(1, len(ranking) + 1))


# ============================================================
# CARDS DE RESUMO
# ============================================================

st.markdown("### 📈 Resumo do ano")

# Cria 4 cards lado a lado com os totais gerais
c1, c2, c3, c4 = st.columns(4)

with c1:
    # st.metric exibe um card com rótulo e valor destacado
    st.metric(
        label="Total de parlamentares",
        value=len(ranking),
    )

with c2:
    st.metric(
        label="Total empenhado",
        value=formatar_moeda_resumida(ranking["total_empenhado"].sum()),
    )

with c3:
    st.metric(
        label="Total pago",
        value=formatar_moeda_resumida(ranking["total_pago"].sum()),
    )

with c4:
    total_emp = ranking["total_empenhado"].sum()
    total_pago = ranking["total_pago"].sum()
    execucao_geral = (total_pago / total_emp * 100) if total_emp > 0 else 0
    st.metric(
        label="Execução geral",
        value=f"{execucao_geral:.1f}%".replace(".", ","),
    )

st.divider()


# ============================================================
# GRÁFICO DE BARRAS — TOP 20
# ============================================================

st.markdown("### 🏆 Top 20 por valor empenhado")

# Pega apenas os 20 primeiros para o gráfico não ficar poluído
top20 = ranking.head(20)

# Cria o gráfico de barras horizontais com plotly
fig = px.bar(
    top20,
    x="total_empenhado",     # eixo X: valor empenhado
    y="nomeAutor",           # eixo Y: nome do parlamentar
    orientation="h",          # "h" = horizontal
    color="tipo",             # cores diferentes por tipo (deputado/senador)
    hover_data=["partido", "uf", "execucao"],  # dados ao passar o mouse
    labels={
        "total_empenhado": "Total Empenhado (R$)",
        "nomeAutor": "Parlamentar",
        "tipo": "Tipo",
    },
    color_discrete_map={
        # define cores específicas para cada tipo
        "Deputado Federal": "#2e6da4",
        "Senador": "#e07b39",
    },
)

# Ajusta o layout do gráfico
fig.update_layout(
    yaxis={"categoryorder": "total ascending"},  # ordena do menor para maior (de baixo pra cima)
    height=600,               # altura em pixels
    showlegend=True,
    plot_bgcolor="white",     # fundo branco
    paper_bgcolor="white",
    margin=dict(l=200),       # margem esquerda maior para os nomes caberem
)

# Exibe o gráfico no Streamlit
st.plotly_chart(fig, use_container_width=True)
# use_container_width=True faz o gráfico ocupar toda a largura disponível

st.divider()


# ============================================================
# TABELA COMPLETA DO RANKING
# ============================================================

st.markdown("### 📋 Ranking completo")

# Prepara o DataFrame para exibição — formata os valores
tabela_exibicao = pd.DataFrame({
    "Pos.": ranking["posição"],
    "Parlamentar": ranking["nomeAutor"].apply(limpar_nome),
    "Partido": ranking["partido"].apply(lambda x: valor_ou_traco(x) if x else "—"),
    "UF": ranking["uf"],
    "Tipo": ranking["tipo"],
    "Emendas": ranking["quantidade_emendas"],
    "Total Empenhado": ranking["total_empenhado"].apply(formatar_moeda),
    "Total Pago": ranking["total_pago"].apply(formatar_moeda),
    "Execução": ranking["execucao"],
})

# st.dataframe exibe a tabela interativa
# o usuário pode ordenar clicando nos cabeçalhos das colunas
st.dataframe(
    tabela_exibicao,
    use_container_width=True,
    hide_index=True,          # esconde o índice numérico do pandas
    height=500,               # altura com scroll
)

# Botão para baixar os dados como CSV
# to_csv exporta o DataFrame para formato CSV
# encode define a codificação para acentos funcionarem
csv = ranking.to_csv(index=False, encoding="utf-8-sig")

st.download_button(
    label="⬇️ Baixar dados em CSV",
    data=csv,
    file_name=f"ranking_emendas_{ano}.csv",
    mime="text/csv",  # tipo do arquivo para o navegador reconhecer
)
