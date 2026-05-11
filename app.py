# ============================================================
# app.py
# Arquivo principal do projeto — é o primeiro arquivo que o
# Streamlit executa quando alguém acessa o site.
# Define a navegação, visual geral e configurações da aplicação.
# ============================================================

# streamlit é a biblioteca principal do projeto
# "as st" cria um apelido — em vez de escrever "streamlit.title()"
# escrevemos apenas "st.title()" — muito mais prático
import streamlit as st


# ============================================================
# CONFIGURAÇÃO GERAL DA PÁGINA
# ============================================================

# st.set_page_config define as configurações globais do site
# IMPORTANTE: deve ser o primeiro comando Streamlit do arquivo
# se colocar depois de outro st.algo(), vai dar erro
st.set_page_config(
    page_title="Emendas Parlamentares",  # título na aba do navegador
    page_icon="🏛️",                      # ícone na aba do navegador
    layout="wide",                        # usa toda a largura da tela
    initial_sidebar_state="expanded",     # menu lateral aberto por padrão
)


# ============================================================
# VERIFICAÇÃO DA CHAVE DE API
# ============================================================

# st.secrets é onde o Streamlit guarda informações sensíveis
# como a chave da API — ela nunca aparece no código ou no GitHub
# No Streamlit Cloud você cadastra os secrets pelo painel
# Em desenvolvimento local, fica num arquivo .streamlit/secrets.toml

# Verifica se a chave foi configurada
# Se não estiver configurada, o site exibe uma mensagem de erro
if "api_key" not in st.secrets:
    st.error(
        "⚠️ Chave da API não configurada. "
        "Adicione a chave em Settings → Secrets no Streamlit Cloud."
    )
    # st.stop() interrompe a execução do código aqui
    # nada abaixo dessa linha será executado
    st.stop()

# Se chegou aqui, a chave existe — guarda numa variável
# para usar em todo o projeto via st.session_state
# session_state é como uma "memória" que persiste enquanto
# o usuário está navegando no site
if "api_key" not in st.session_state:
    st.session_state.api_key = st.secrets["api_key"]


# ============================================================
# ESTILO VISUAL GLOBAL
# ============================================================

# st.markdown com unsafe_allow_html=True permite injetar CSS
# CSS é a linguagem que controla cores, fontes e espaçamentos
# Aqui definimos o visual geral que vale para todas as telas
st.markdown("""
    <style>
        /* Remove o espaço padrão no topo da página */
        .block-container {
            padding-top: 2rem;
        }
        
        /* Estilo dos cards de métricas */
        [data-testid="metric-container"] {
            background-color: #f0f4f8;
            border: 1px solid #d0dce8;
            border-radius: 8px;
            padding: 16px;
        }
        
        /* Cor do valor principal dos cards */
        [data-testid="metric-container"] [data-testid="stMetricValue"] {
            color: #1a3a5c;
            font-size: 1.4rem;
        }
        
        /* Estilo dos botões */
        .stButton button {
            background-color: #1a3a5c;
            color: white;
            border-radius: 6px;
            border: none;
            padding: 0.4rem 1rem;
        }
        
        /* Estilo dos botões ao passar o mouse */
        .stButton button:hover {
            background-color: #2e6da4;
        }
        
        /* Remove a borda padrão das tabelas */
        .stDataFrame {
            border: none;
        }
    </style>
""", unsafe_allow_html=True)


# ============================================================
# CABEÇALHO PRINCIPAL
# ============================================================

# Divide o topo em duas colunas — logo à esquerda, título à direita
# [1, 4] significa proporção: 1 parte para a primeira, 4 para a segunda
col_logo, col_titulo = st.columns([1, 4])

with col_logo:
    # Exibe o ícone grande centralizado
    # "with col_logo:" significa: coloca o que está dentro dessa coluna
    st.markdown(
        "<h1 style='text-align:center; font-size:4rem;'>🏛️</h1>",
        unsafe_allow_html=True
    )

with col_titulo:
    st.markdown(
        "<h1 style='color:#1a3a5c; margin-bottom:0;'>Emendas Parlamentares</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='color:#666; font-size:1.1rem; margin-top:0;'>"
        "Plataforma de transparência para o eleitor brasileiro — dados públicos, sem julgamentos."
        "</p>",
        unsafe_allow_html=True
    )

# Linha divisória
st.divider()


# ============================================================
# CONTEÚDO DA PÁGINA INICIAL
# ============================================================

# st.markdown exibe texto formatado — o # indica título, ** indica negrito
st.markdown("## 📌 Como usar esta plataforma")

# Divide em 3 colunas iguais para mostrar as funcionalidades
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **🔍 Buscar**
    
    Pesquise por parlamentar, partido, estado ou município.
    Também é possível buscar pelo recebedor das emendas —
    uma ONG, empresa ou prefeitura específica.
    """)

with col2:
    st.markdown("""
    **📊 Analisar**
    
    Veja o ranking geral de parlamentares por volume de emendas,
    com detalhes de execução, áreas temáticas e
    distribuição geográfica dos recursos.
    """)

with col3:
    st.markdown("""
    **⚖️ Comparar**
    
    Selecione dois parlamentares e veja os dados
    lado a lado — valores empenhados, pagos,
    destinos e projetos legislativos.
    """)

st.divider()

# Instrução para o usuário navegar
st.markdown("""
    <p style='text-align:center; color:#666; font-size:1rem;'>
    👈 Use o menu lateral para navegar entre as seções da plataforma.
    </p>
""", unsafe_allow_html=True)


# ============================================================
# RODAPÉ
# ============================================================

st.markdown("""
    <hr style='margin-top:3rem; border-color:#d0dce8;'>
    <p style='text-align:center; color:#999; font-size:0.85rem;'>
    Dados obtidos via API do 
    <a href='https://portaldatransparencia.gov.br' target='_blank'>Portal da Transparência</a> 
    e da 
    <a href='https://dadosabertos.camara.leg.br' target='_blank'>Câmara dos Deputados</a>. 
    Atualização automática a cada hora. 
    Uso exclusivo de dados públicos conforme Decreto nº 8.777/2016.
    </p>
""", unsafe_allow_html=True)
