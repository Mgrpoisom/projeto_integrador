import random
from datetime import date, timedelta
from app import app, db
from models import Crianca, Unidade
import priority_engine

# Listas para dados fakes brasileiros
nomes = ["Enzo", "Valentina", "Miguel", "Alice", "Arthur", "Sophia", "Heitor", "Helena", "Théo", "Laura", "Gabriel", "Manuela", "Bernardo", "Bia", "Samuel", "Isabella"]
sobrenomes = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho"]
bairros = ["Centro", "Jardim América", "Vila Nova", "Santo Antônio", "Bela Vista", "Parque das Nações", "Santa Cruz", "Ipê", "Salgado Filho"]

def gerar_data_nascimento():
    # Gera crianças entre 0 e 4 anos
    hoje = date.today()
    dias_atras = random.randint(30, 1400)
    return hoje - timedelta(days=dias_atras)

def seed():
    with app.app_context():
        print("Limpando dados antigos (opcional)...")
        # Se quiser limpar antes: Crianca.query.delete()
        
        unidade = Unidade.query.first()
        if not unidade:
            print("Unidade não encontrada!")
            return

        print("Gerando 100 cadastros fakes...")
        for i in range(100):
            nome_completo = f"{random.choice(nomes)} {random.choice(sobrenomes)} {random.choice(sobrenomes)}"
            responsavel = f"{random.choice(nomes)} {random.choice(sobrenomes)}"
            data_nasc = gerar_data_nascimento()
            bairro = random.choice(bairros)
            telefone = f"(11) 9{random.randint(7000, 9999)}-{random.randint(1000, 9999)}"
            
            categoria = priority_engine.atribuir_categoria(data_nasc)
            vulnerabilidade = {
                "mae_trabalha": random.choice([True, False]),
                "baixa_renda": random.choice([True, False]),
                "risco_social": random.choice([True, False, False, False]), # Menos comum
                "deficiencia": random.choice([True, False, False, False, False])
            }
            pontuacao = priority_engine.calcular_pontuacao(vulnerabilidade)
            
            # Algumas já entram matriculadas, outras na fila
            status = 'matriculada' if i < unidade.capacidade_total else 'aguardando'
            
            nova = Crianca(
                nome=nome_completo,
                data_nascimento=data_nasc,
                responsavel=responsavel,
                bairro=bairro,
                telefone=telefone,
                categoria=categoria,
                pontuacao=pontuacao,
                status=status
            )
            db.session.add(nova)
        
        db.session.commit()
        print("Sucesso! 100 registros inseridos.")

if __name__ == "__main__":
    seed()
