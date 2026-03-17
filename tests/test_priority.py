import pytest
from datetime import date, timedelta
from priority_engine import atribuir_categoria, calcular_pontuacao

def test_atribuir_categoria():
    hoje = date.today()
    # Berçário I: 4m a 12m
    b1_nasc = hoje - timedelta(days=180) # ~6 meses
    assert atribuir_categoria(b1_nasc) == "Berçário I"
    
    # Berçário II: 12m a 24m
    b2_nasc = hoje - timedelta(days=400) # ~13 meses
    assert atribuir_categoria(b2_nasc) == "Berçário II"

    # Não elegível
    velho_nasc = hoje - timedelta(days=2000)
    assert atribuir_categoria(velho_nasc) == "Não elegível"

def test_calcular_pontuacao():
    # Caso base
    assert calcular_pontuacao({}) == 0
    
    # Prioridades acumuladas
    dados = {
        'mae_trabalha': True,
        'baixa_renda': True,
        'necessidades_especiais': False
    }
    assert calcular_pontuacao(dados) == 30 # 10 + 20

    # Máximo score
    dados_max = {
        'mae_trabalha': True,
        'baixa_renda': True,
        'necessidades_especiais': True
    }
    assert calcular_pontuacao(dados_max) == 80 # 10 + 20 + 50
