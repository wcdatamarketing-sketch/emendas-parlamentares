# ============================================================
# pages/5_Detalhe_Emenda.py
# Tela de detalhamento de uma emenda específica —
# exibe todas as informações disponíveis sobre uma emenda
# ============================================================

import streamlit as st

# Importamos a função de cache para buscar o detalhe
from utils.cache import cache_detalhe_emenda

# Importamos os formatadores
from utils.formatters import (
    formatar_moeda,
    formatar_data,
    valor_ou_traco,
    limpar_nome,
)


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Detalhe da Emenda — Emendas Parlamentares",
    page_icon="📄",
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
    "<h1 style='color:#1a3a5c;'>📄 Detalhe da Emenda</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "Consulte todas as informações de uma emenda específica "
    "pelo seu código ou número."
)
st.divider()


# ============================================================
# CAMPO DE BUSCA
# ============================================================

col_codigo, col_buscar = st.columns([4, 1])

with col_codigo:
    # O código da emenda é um identificador único
    # geralmente encontrado nas tabelas das outras telas
    codigo_emenda = st.text_input(
        "Código da emenda",
        placeholder="Ex: 39271.1220.0001-01",
    )

with col_buscar:
    # Espaço para alinhar o botão com o campo de texto
    st.markdown("<br>", unsafe_allow_html=True)
    buscar = st.button("🔍 Buscar", use_container_width=True)
    # use_container_width=True faz o botão ocupar toda a largura da coluna

# Só executa se o usuário digitou o código e clicou em buscar
# "buscar" é True quando o botão foi clicado
# "not codigo_emenda" é True quando o campo está vazio
if not codigo_emenda:
    st.info("👆 Digite o código da emenda para consultar os detalhes.")
    st.stop()


# ============================================================
# BUSCA DOS DADOS
# ============================================================

with st.spinner("Buscando detalhes da emenda..."):
    emenda = cache_detalhe_emenda(api_key, codigo_emenda)

# Se não encontrou a emenda
if not emenda:
    st.warning(
        f"Emenda '{codigo_emenda}' não encontrada. "
        "Verifique o código e tente novamente."
    )
    st.stop()


# ============================================================
# FUNÇÃO AUXILIAR PARA EXIBIR CAMPOS
# ============================================================

def campo(rotulo: str, valor) -> None:
    """
    Exibe um campo formatado com rótulo em negrito e valor ao lado.
    Usamos essa função para evitar repetir o mesmo HTML várias vezes.

    rotulo: nome do campo (ex: "Parlamentar")
    valor:  valor a exibir (pode ser nulo — valor_ou_traco trata isso)
    """
    st.markdown(
        f"**{rotulo}:** {valor_ou_traco(valor)}",
        unsafe_allow_html=True
    )


# ============================================================
# DADOS DO AUTOR
# ============================================================

st.markdown("### 👤 Autor da emenda")

col1, col2, col3 = st.columns(3)

with col1:
    campo("Parlamentar", limpar_nome(emenda.get("nomeAutor")))
    # .get() acessa um campo do dicionário de forma segura
    # se o campo não existir, retorna None em vez de dar erro

with col2:
    campo("Partido", emenda.get("partidoAutor"))

with col3:
    campo("Estado (UF)", emenda.get("ufAutor"))

st.divider()


# ============================================================
# DADOS DA EMENDA
# ============================================================

st.markdown("### 📋 Dados da emenda")

col1, col2, col3 = st.columns(3)

with col1:
    campo("Número da emenda", emenda.get("numeroEmenda"))
    campo("Código da emenda", emenda.get("codigoEmenda"))

with col2:
    campo("Tipo de emenda", emenda.get("tipoEmenda"))
    campo("Ano", emenda.get("ano"))

with col3:
    campo("Área temática", emenda.get("funcao"))
    campo("Subfunção", emenda.get("subfuncao"))

st.divider()


# ============================================================
# DADOS FINANCEIROS
# ============================================================

st.markdown("### 💰 Valores")

# Pega os valores do dicionário — .get() retorna 0 se não existir
valor_empenhado = emenda.get("valorEmpenhado", 0)
valor_liquidado = emenda.get("valorLiquidado", 0)
valor_pago = emenda.get("valorPago", 0)

# Exibe os três valores em cards lado a lado
c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        label="💼 Valor empenhado",
        value=formatar_moeda(valor_empenhado),
        help="Valor comprometido no orçamento — promessa de pagamento"
        # help exibe um tooltip (?) ao lado do rótulo com explicação
    )

with c2:
    st.metric(
        label="✅ Valor liquidado",
        value=formatar_moeda(valor_liquidado),
        help="Valor confirmado após entrega do serviço ou produto"
    )

with c3:
    st.metric(
        label="💸 Valor pago",
        value=formatar_moeda(valor_pago),
        help="Valor efetivamente transferido ao favorecido"
    )

# Barra de progresso da execução
# mostra visualmente quanto do empenhado foi pago
st.markdown("<br>", unsafe_allow_html=True)

if valor_empenhado > 0:
    # Calcula o percentual como número entre 0 e 1
    # (o st.progress espera um valor entre 0.0 e 1.0)
    percentual = min(valor_pago / valor_empenhado, 1.0)

    st.markdown(f"**Execução:** {percentual * 100:.1f}%".replace(".", ","))

    # st.progress exibe uma barra de progresso visual
    st.progress(percentual)

st.divider()


# ============================================================
# DADOS DO FAVORECIDO
# ============================================================

st.markdown("### 🏢 Favorecido (quem recebeu)")

col1, col2, col3 = st.columns(3)

with col1:
    campo("Nome", limpar_nome(emenda.get("nomeFavorecido")))

with col2:
    campo("Município", emenda.get("municipioFavorecido"))
    campo("Estado (UF)", emenda.get("ufFavorecido"))

with col3:
    campo("CNPJ/CPF", emenda.get("cnpjCpfFavorecido"))

st.divider()


# ============================================================
# INFORMAÇÕES DE CONVÊNIO
# ============================================================

st.markdown("### 📎 Convênio e rastreabilidade")

# Verifica se há convênio vinculado a essa emenda
numero_convenio = emenda.get("numeroConvenio")

if numero_convenio:
    # Se tem convênio, exibe os dados e o link para o Transferegov
    col1, col2 = st.columns(2)

    with col1:
        campo("Número do convênio", numero_convenio)
        campo("Situação do convênio", emenda.get("situacaoConvenio"))

    with col2:
        campo("Data de início", formatar_data(emenda.get("dataInicioConvenio")))
        campo("Data de fim", formatar_data(emenda.get("dataFimConvenio")))

    # Link para acompanhar no Transferegov
    # o Transferegov é o sistema federal de prestação de contas
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"🔗 [Acompanhar no Transferegov.br]"
        f"(https://transferegov.sistema.gov.br/voluntarias/consulta/"
        f"consultarConvenio.do?numero={numero_convenio})",
        unsafe_allow_html=True
    )

else:
    # Se não tem convênio, pode ser transferência especial
    # que tem menos rastreabilidade — informamos o usuário
    st.info(
        "ℹ️ Esta emenda não possui convênio vinculado. "
        "Pode se tratar de uma Transferência Especial, modalidade que "
        "não exige celebração de convênio e tem rastreabilidade reduzida."
    )

st.divider()


# ============================================================
# DADOS BRUTOS (para usuários avançados)
# ============================================================

# expander cria uma seção recolhível — o usuário clica para expandir
# útil para informações secundárias que não precisam estar sempre visíveis
with st.expander("🔧 Ver dados brutos (JSON completo da API)"):
    st.markdown(
        "Todos os campos retornados pela API do Portal da Transparência:"
    )
    # st.json exibe um dicionário formatado e colorido
    # facilita a leitura para usuários técnicos
    st.json(emenda)


# ============================================================
# BOTÃO DE VOLTAR
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)

# Cria coluna centralizada para o botão ficar no meio da tela
col_esq, col_btn, col_dir = st.columns([3, 2, 3])

with col_btn:
    if st.button("← Voltar ao Ranking", use_container_width=True):
        # switch_page navega para outra página do Streamlit
        # o nome deve corresponder ao arquivo em pages/
        st.switch_page("pages/1_Ranking.py")
