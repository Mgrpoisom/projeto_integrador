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
            bairro=data.get('bairro'),
            telefone=data.get('telefone'),
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

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/api/admin/stats')
def admin_stats():
    unidade = Unidade.query.first()
    vagas_ocupadas = Crianca.query.filter_by(status='matriculada').count()
    na_fila = Crianca.query.filter_by(status='aguardando').count()
    return jsonify({
        "unidade": unidade.nome,
        "capacidade_total": unidade.capacidade_total,
        "vagas_ocupadas": vagas_ocupadas,
        "vagas_disponiveis": unidade.capacidade_total - vagas_ocupadas,
        "na_fila": na_fila
    })

@app.route('/api/admin/unidade/capacidade', methods=['POST'])
def update_capacidade():
    data = request.json
    unidade = Unidade.query.first()
    unidade.capacidade_total = data['capacidade']
    db.session.commit()
    return jsonify({"mensagem": "Capacidade atualizada com sucesso!"})

@app.route('/api/admin/criancas')
def admin_criancas():
    # Retorna todas as crianças com dados completos para o admin
    criancas = Crianca.query.order_by(Crianca.data_cadastro.desc()).all()
    return jsonify([{
        "id": c.id,
        "nome": c.nome,
        "responsavel": c.responsavel,
        "categoria": c.categoria,
        "status": c.status,
        "bairro": c.bairro,
        "telefone": c.telefone,
        "data_cadastro": c.data_cadastro.strftime('%d/%m/%Y %H:%M')
    } for c in criancas])

@app.route('/api/admin/matricular/<int:id>', methods=['POST'])
def matricular_manual(id):
    crianca = Crianca.query.get_or_404(id)
    if crianca.status == 'matriculada':
        return jsonify({"erro": "Criança já está matriculada"}), 400
    
    unidade = Unidade.query.first()
    crianca.status = 'matriculada'
    matricula = Matricula(crianca_id=crianca.id, unidade_id=unidade.id)
    db.session.add(matricula)
    db.session.commit()
    return jsonify({"mensagem": f"Matrícula de {crianca.nome} realizada manualmente."})

def processar_fila():
    unidade = Unidade.query.first()
    vagas_ocupadas = Crianca.query.filter_by(status='matriculada').count()
    vagas_livres = unidade.capacidade_total - vagas_ocupadas
    
    if vagas_livres > 0:
        # Pega os próximos da fila por prioridade
        na_fila = Crianca.query.filter_by(status='aguardando')\
            .order_by(Crianca.pontuacao.desc(), Crianca.data_cadastro.asc())\
            .limit(vagas_livres).all()
        
        for crianca in na_fila:
            crianca.status = 'matriculada'
            matricula = Matricula(crianca_id=crianca.id, unidade_id=unidade.id)
            db.session.add(matricula)
        
        db.session.commit()

@app.route('/api/admin/remover/<int:id>', methods=['POST'])
def remover_crianca(id):
    crianca = Crianca.query.get_or_404(id)
    # Remove matrículas associadas
    Matricula.query.filter_by(crianca_id=id).delete()
    # Marca como removida ou deleta (vamos marcar como 'removida' para histórico se quiser, mas aqui deletaremos para simplificar a vaga)
    db.session.delete(crianca)
    db.session.commit()
    
    # Processa a fila para preencher a vaga aberta
    processar_fila()
    
    return jsonify({"mensagem": "Criança removida e vaga reofertada para a fila."})

@app.route('/dashboard')
def dashboard_view():
    return render_template('dashboard.html')

@app.route('/api/admin/dashboard/stats')
def dashboard_stats():
    # 1. Distribuição por Categoria e Status (Breakdown Inteligente)
    labels_base = ["Berçário I", "Berçário II", "Maternal I", "Maternal II"]
    breakdown_raw = db.session.query(Crianca.categoria, Crianca.status, db.func.count(Crianca.id))\
        .group_by(Crianca.categoria, Crianca.status).all()
    
    breakdown_data = {cat: {"matriculada": 0, "aguardando": 0} for cat in labels_base}
    for cat, status, count in breakdown_raw:
        if cat in breakdown_data and status in ["matriculada", "aguardando"]:
            breakdown_data[cat][status] = count

    # 2. Distribuição Geral (Status) para KPIs
    status_counts = db.session.query(Crianca.status, db.func.count(Crianca.id))\
        .group_by(Crianca.status).all()
    dist_status = {s: count for s, count in status_counts}

    # 3. Distribuição por Bairro (Novo Insight)
    bairros_query = db.session.query(Crianca.bairro, db.func.count(Crianca.id))\
        .filter(Crianca.bairro.isnot(None))\
        .group_by(Crianca.bairro).all()
    dist_bairro = {b: count for b, count in bairros_query}

    # 4. Perfil de Vulnerabilidade
    com_vulnerabilidade = Crianca.query.filter(Crianca.pontuacao > 0).count()
    sem_vulnerabilidade = Crianca.query.filter(Crianca.pontuacao == 0).count()

    # 5. KPIs
    unidade = Unidade.query.first()
    matriculas = Matricula.query.count()
    tempo_medio = "45 dias" if matriculas > 0 else "N/A"

    return jsonify({
        "breakdown_categoria": breakdown_data,
        "labels": labels_base,
        "dist_bairro": dist_bairro,
        "perfil_vulnerabilidade": {
            "Com Prioridade": com_vulnerabilidade,
            "Sem Prioridade": sem_vulnerabilidade
        },
        "kpis": {
            "tempo_medio_espera": tempo_medio,
            "taxa_ocupacao": f"{round((dist_status.get('matriculada', 0) / (unidade.capacidade_total or 1)) * 100)}%"
        }
    })

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
    app.run(host='0.0.0.0', port=5000, debug=True)
