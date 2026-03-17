from datetime import date

def calcular_idade(data_nascimento):
    hoje = date.today()
    return hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))

def atribuir_categoria(data_nascimento):
    """
    Berçário I: 4 meses a 1 ano.
    Berçário II: 1 a 2 anos.
    Maternal I: cerca de 2 anos.
    Maternal II: cerca de 3 anos.
    """
    hoje = date.today()
    meses = (hoje.year - data_nascimento.year) * 12 + hoje.month - data_nascimento.month
    if hoje.day < data_nascimento.day:
        meses -= 1

    if 4 <= meses < 12:
        return "Berçário I"
    elif 12 <= meses < 24:
        return "Berçário II"
    elif 24 <= meses < 36:
        return "Maternal I"
    elif 36 <= meses < 48:
        return "Maternal II"
    else:
        return "Não elegível"

def calcular_pontuacao(dados_vulnerabilidade):
    """
    Calcula pontuação baseada em critérios socioeconômicos.
    Exemplo: 
    - Mãe trabalhadora: +10
    - Baixa renda: +20
    - Necessidades especiais: +50
    """
    score = 0
    if dados_vulnerabilidade.get('mae_trabalha'):
        score += 10
    if dados_vulnerabilidade.get('baixa_renda'):
        score += 20
    if dados_vulnerabilidade.get('necessidades_especiais'):
        score += 50
    return score
