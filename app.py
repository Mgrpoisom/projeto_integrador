from flask import Flask, render_template, jsonify, request
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
from database import db
from models import Crianca, Unidade, Matricula
import priority_engine

def create_app():
    app = Flask(__name__)
    # Usando sqlite para facilitar prototipagem
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///creche.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

app = create_app()

def setup_app():
    with app.app_context():
        db.create_all()
        # Criar unidade padrão se não existir
        if not Unidade.query.first():
            u = Unidade(nome="Creche Municipal Sagrada Família", capacidade_total=5)
            db.session.add(u)
            db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cadastrar', methods=['POST'])
def cadastrar():
    data = request.json
    try:
        data_nasc = datetime.strptime(data['data_nascimento'], '%Y-%m-%d').date()
        categoria = priority_engine.atribuir_categoria(data_nasc)
        
        if categoria == "Não elegível":
            return jsonify({"erro": "Idade fora da faixa atendida pela creche"}), 400

        pontuacao = priority_engine.calcular_pontuacao(data.get('vulnerabilidade', {}))
        
        nova_crianca = Crianca(
            nome=data['nome'],
            data_nascimento=data_nasc,
            responsavel=data['responsavel'],
            categoria=categoria,
            pontuacao=pontuacao,
            status='aguardando'
        )
        db.session.add(nova_crianca)
        db.session.commit()

        # Tentar matricular se houver vaga
        unidade = Unidade.query.first()
        vagas_ocupadas = Crianca.query.filter_by(status='matriculada').count()
        
        if vagas_ocupadas < unidade.capacidade_total:
            nova_crianca.status = 'matriculada'
            matricula = Matricula(crianca_id=nova_crianca.id, unidade_id=unidade.id)
            db.session.add(matricula)
            db.session.commit()
            return jsonify({"status": "matriculada", "mensagem": "Matrícula realizada com sucesso!"})
        
        return jsonify({"status": "aguardando", "mensagem": "Criança inserida na lista de espera."})
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

@app.route('/api/fila')
def ver_fila():
    fila = Crianca.query.filter_by(status='aguardando').order_by(Crianca.pontuacao.desc(), Crianca.data_cadastro.asc()).all()
    resultado = [{
        "nome": c.nome,
        "categoria": c.categoria,
        "pontuacao": c.pontuacao,
        "posicao": i + 1
    } for i, c in enumerate(fila)]
    return jsonify(resultado)

@app.route('/api/status')
def status():
    unidade = Unidade.query.first()
    vagas_ocupadas = Crianca.query.filter_by(status='matriculada').count()
    return jsonify({
        "status": "online", 
        "projeto": "Sistema de Gestão de Creches",
        "unidade": unidade.nome,
        "vagas_disponiveis": (unidade.capacidade_total - vagas_ocupadas) if unidade else 0
    })

if __name__ == '__main__':
    setup_app()
    app.run(debug=True)
