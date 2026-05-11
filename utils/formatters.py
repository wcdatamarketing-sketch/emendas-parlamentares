# ============================================================
# utils/formatters.py
# Caixinha de ferramentas para formatar dados antes de exibir
# na tela — moeda, datas, percentuais e valores nulos
# ============================================================


# ============================================================
# FORMATAÇÃO DE MOEDA
# ============================================================

def formatar_moeda(valor) -> str:
    """
    Converte um número em string formatada como moeda brasileira.
    Exemplo: 15000000.5 → "R$ 15.000.000,50"
    
    valor: número inteiro ou decimal (pode vir como string da API)
    retorna: string formatada como moeda
    """
    
    # Tenta converter o valor para float
    # "try/except" é como dizer: "tenta fazer isso,
    # mas se der erro, faz aquilo outro"
    try:
        # float() converte qualquer número para decimal
        valor_float = float(valor)
    except (TypeError, ValueError):
        # Se não conseguir converter (ex: valor é None ou texto)
        # retorna um traço indicando que não há valor
        return "R$ —"
    
    # Formata o número no padrão brasileiro
    # {:,.2f} formata com 2 casas decimais e separador de milhar
    # depois substituímos o padrão americano pelo brasileiro:
    # ponto vira vírgula e vírgula vira ponto
    valor_formatado = f"{valor_float:,.2f}"
    valor_formatado = valor_formatado.replace(",", "X")  # , → X (temporário)
    valor_formatado = valor_formatado.replace(".", ",")  # . → ,
    valor_formatado = valor_formatado.replace("X", ".")  # X → .
    
    return f"R$ {valor_formatado}"


def formatar_moeda_resumida(valor) -> str:
    """
    Formata valores grandes de forma resumida para exibir em cards.
    Exemplo: 15000000 → "R$ 15,0 mi"
             1500000000 → "R$ 1,5 bi"
    
    valor: número inteiro ou decimal
    retorna: string resumida
    """
    
    try:
        valor_float = float(valor)
    except (TypeError, ValueError):
        return "R$ —"
    
    # Bilhões — divide por 1 bilhão e formata com 1 casa decimal
    if valor_float >= 1_000_000_000:
        return f"R$ {valor_float / 1_000_000_000:.1f} bi"
    
    # Milhões — divide por 1 milhão
    if valor_float >= 1_000_000:
        return f"R$ {valor_float / 1_000_000:.1f} mi"
    
    # Mil — divide por 1000
    if valor_float >= 1_000:
        return f"R$ {valor_float / 1_000:.1f} mil"
    
    # Valores menores que mil — mostra completo
    return formatar_moeda(valor_float)


# ============================================================
# FORMATAÇÃO DE PERCENTUAL
# ============================================================

def formatar_percentual(valor) -> str:
    """
    Converte um número decimal em percentual formatado.
    Exemplo: 0.873 → "87,3%"
             87.3  → "87,3%"  (aceita os dois formatos)
    
    valor: número entre 0 e 1 OU entre 0 e 100
    retorna: string formatada como percentual
    """
    
    try:
        valor_float = float(valor)
    except (TypeError, ValueError):
        return "—%"
    
    # Se o valor já veio em percentual (ex: 87.3), usa direto
    # Se veio como decimal (ex: 0.873), multiplica por 100
    if valor_float <= 1.0:
        valor_float = valor_float * 100
    
    # Formata com 1 casa decimal no padrão brasileiro
    return f"{valor_float:.1f}%".replace(".", ",")


def calcular_percentual_execucao(valor_empenhado, valor_pago) -> str:
    """
    Calcula e formata o percentual de execução de uma emenda.
    Execução = quanto do valor empenhado foi de fato pago.
    Exemplo: empenhado=1000, pago=873 → "87,3%"
    
    valor_empenhado: valor total comprometido
    valor_pago:      valor efetivamente pago
    retorna:         string com o percentual de execução
    """
    
    try:
        empenhado = float(valor_empenhado)
        pago = float(valor_pago)
    except (TypeError, ValueError):
        return "—%"
    
    # Evita divisão por zero — se não há valor empenhado
    # não faz sentido calcular percentual
    if empenhado == 0:
        return "—%"
    
    percentual = (pago / empenhado) * 100
    
    # Limita a 100% — em alguns casos o valor pago pode
    # ultrapassar levemente o empenhado por correções
    percentual = min(percentual, 100.0)
    
    return f"{percentual:.1f}%".replace(".", ",")


# ============================================================
# FORMATAÇÃO DE DATAS
# ============================================================

def formatar_data(data_str) -> str:
    """
    Converte data do formato da API para o formato brasileiro.
    Exemplo: "2024-03-15" → "15/03/2024"
             "2024-03-15T00:00:00" → "15/03/2024"
    
    data_str: string de data vinda da API
    retorna:  string no formato DD/MM/AAAA
    """
    
    # Se não veio nenhum valor, retorna traço
    if not data_str:
        return "—"
    
    try:
        # Pega só os primeiros 10 caracteres (a parte da data)
        # ignorando a hora que às vezes vem junto (ex: T00:00:00)
        data_str = str(data_str)[:10]
        
        # Separa ano, mês e dia pelo hífen
        # "split" divide a string em partes usando o separador informado
        partes = data_str.split("-")
        
        # Se não tiver exatamente 3 partes, o formato é inválido
        if len(partes) != 3:
            return data_str  # devolve como veio
        
        ano, mes, dia = partes
        
        # Remonta no formato brasileiro DD/MM/AAAA
        return f"{dia}/{mes}/{ano}"
    
    except Exception:
        # Se qualquer coisa der errado, devolve o valor original
        return str(data_str)


# ============================================================
# TRATAMENTO DE VALORES NULOS
# ============================================================

def valor_ou_traco(valor, sufixo: str = "") -> str:
    """
    Retorna o valor formatado ou um traço se o valor for nulo.
    Útil para campos que a API às vezes não preenche.
    Exemplo: "SP" → "SP"
             None → "—"
             ""   → "—"
    
    valor:  qualquer valor que pode ser nulo
    sufixo: texto opcional para adicionar após o valor (ex: " votos")
    retorna: string com o valor ou "—"
    """
    
    # Verifica se o valor é nulo ou string vazia
    if valor is None or str(valor).strip() == "":
        return "—"
    
    return f"{valor}{sufixo}"


def limpar_nome(nome) -> str:
    """
    Padroniza nomes vindos da API — remove espaços extras
    e coloca em formato título (primeira letra maiúscula).
    Exemplo: "SILVA, JOÃO DA  " → "Silva, João Da"
    
    nome:    string com o nome como veio da API
    retorna: string com o nome padronizado
    """
    
    if not nome:
        return "—"
    
    # strip() remove espaços no início e no fim
    # title() coloca a primeira letra de cada palavra em maiúscula
    return str(nome).strip().title()


def formatar_numero(valor) -> str:
    """
    Formata um número inteiro com separador de milhar brasileiro.
    Exemplo: 1500 → "1.500"
             300  → "300"
    
    valor:   número inteiro
    retorna: string formatada
    """
    
    try:
        valor_int = int(float(valor))
    except (TypeError, ValueError):
        return "—"
    
    # {:,} adiciona separador de milhar americano (vírgula)
    # depois substituímos pela vírgula pelo ponto (padrão BR)
    return f"{valor_int:,}".replace(",", ".")
