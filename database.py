from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# ─────────────────────────────────────────
# TABELA DE USUÁRIOS
# Quem pode acessar o sistema
# ─────────────────────────────────────────
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    perfil = db.Column(db.String(20), default='operador')  # admin ou operador
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def definir_senha(self, senha):
        # Criptografa a senha antes de salvar
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        # Confere se a senha digitada bate com a criptografada
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f'<Usuario {self.email}>'


# ─────────────────────────────────────────
# TABELA DE CONTATOS
# As 1000+ pessoas da sua lista
# ─────────────────────────────────────────
class Contato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    telefone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(150), nullable=True)
    regiao = db.Column(db.String(100), nullable=True)
    tag = db.Column(db.String(100), nullable=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Contato {self.nome}>'


# ─────────────────────────────────────────
# TABELA DE GRUPOS
# Os grupos de WhatsApp organizados
# ─────────────────────────────────────────
class Grupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.String(300), nullable=True)
    limite = db.Column(db.Integer, default=150)
    mensagem_boas_vindas = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    contatos = db.relationship('Contato', backref='grupo', lazy=True)

    def total_membros(self):
        return len(self.contatos)

    def __repr__(self):
        return f'<Grupo {self.nome}>'


# ─────────────────────────────────────────
# TABELA DE CAMPANHAS
# Mensagens enviadas para os grupos
# ─────────────────────────────────────────
class Campanha(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='rascunho')  # rascunho, enviada, agendada
    agendado_para = db.Column(db.DateTime, nullable=True)
    enviado_em = db.Column(db.DateTime, nullable=True)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Campanha {self.titulo}>'


# ─────────────────────────────────────────
# TABELA DE LOGS
# Registro de tudo que acontece no sistema
# ─────────────────────────────────────────
class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    acao = db.Column(db.String(200), nullable=False)
    usuario_email = db.Column(db.String(150), nullable=True)
    detalhes = db.Column(db.Text, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Log {self.acao}>'
