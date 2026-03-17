from datetime import datetime
from database import db

class Unidade(db.Model):
    __tablename__ = 'unidades'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    capacidade_total = db.Column(db.Integer, default=5)
    
    def __repr__(self):
        return f'<Unidade {self.nome}>'

class Crianca(db.Model):
    __tablename__ = 'criancas'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    responsavel = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(20)) # B1, B2, M1, M2
    pontuacao = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='aguardando') # aguardando, matriculada
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Crianca {self.nome}>'

class Matricula(db.Model):
    __tablename__ = 'matriculas'
    id = db.Column(db.Integer, primary_key=True)
    crianca_id = db.Column(db.Integer, db.ForeignKey('criancas.id'), nullable=False)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id'), nullable=False)
    data_matricula = db.Column(db.DateTime, default=datetime.utcnow)
    
    crianca = db.relationship('Crianca', backref=db.backref('matricula', uselist=False))
    unidade = db.relationship('Unidade', backref=db.backref('matriculas', lazy=True))
