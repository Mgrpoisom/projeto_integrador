from app import app, db, Unidade, Crianca
from datetime import date, timedelta

def test_fluxo_vagas(client):
    # Setup: Garantir unidade com 2 vagas para teste rápido
    with app.app_context():
        db.create_all()
        u = Unidade.query.first()
        u.capacidade_total = 2
        db.session.commit()

    # 1. Matricular 2 crianças (deve preencher as vagas)
    for i in range(2):
        client.post('/api/cadastrar', json={
            "nome": f"Criança {i}",
            "data_nascimento": (date.today() - timedelta(days=500)).isoformat(),
            "responsavel": "Responsável",
            "vulnerabilidade": {}
        })

    # 2. Tentar cadastrar a 3ª criança (deve ir para a fila)
    res = client.post('/api/cadastrar', json={
        "nome": "Criança Fila",
        "data_nascimento": (date.today() - timedelta(days=500)).isoformat(),
        "responsavel": "Responsável Fila",
        "vulnerabilidade": {"necessidades_especiais": True}
    })
    assert res.json['status'] == 'aguardando'

    # 3. Verificar se a fila está correta
    res_fila = client.get('/api/fila')
    assert len(res_fila.json) == 1
    assert res_fila.json[0]['nome'] == "Criança Fila"
    assert res_fila.json[0]['pontuacao'] == 50
