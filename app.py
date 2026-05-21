from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from database import db, Usuario, Log
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'bbrain-dev-key')

# ─────────────────────────────────────────
# CONFIGURAÇÃO DO BANCO DE DADOS
# Cria um arquivo bbrain.db localmente
# ─────────────────────────────────────────
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///bbrain.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ─────────────────────────────────────────
# CRIA AS TABELAS E O ADMIN INICIAL
# Roda só uma vez quando o sistema inicia
# ─────────────────────────────────────────
with app.app_context():
    db.create_all()

    # Se não existir nenhum usuário, cria o admin padrão
    if not Usuario.query.first():
        admin = Usuario(
            nome='Admin',
            email='admin@bbrain.com',
            perfil='admin'
        )
        admin.definir_senha('bbrain123')
        db.session.add(admin)
        db.session.commit()
        print('✅ Admin criado com sucesso!')


# ─────────────────────────────────────────
# ROTAS
# ─────────────────────────────────────────

@app.route('/')
def index():
    if 'usuario' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    senha = request.form.get('senha')

    usuario = Usuario.query.filter_by(email=email, ativo=True).first()

    if usuario and usuario.verificar_senha(senha):
        session['usuario'] = usuario.email
        session['nome'] = usuario.nome
        session['perfil'] = usuario.perfil

        # Registra o login no log
        log = Log(acao='login', usuario_email=usuario.email, detalhes='Login realizado com sucesso')
        db.session.add(log)
        db.session.commit()

        return redirect(url_for('dashboard'))

    flash('Email ou senha incorretos.')
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('index'))

    from database import Contato, Grupo, Campanha
    total_contatos = Contato.query.count()
    total_grupos = Grupo.query.filter_by(ativo=True).count()
    total_campanhas = Campanha.query.filter_by(status='enviada').count()
    total_usuarios = Usuario.query.filter_by(ativo=True).count()

    return render_template('dashboard.html',
        nome=session['nome'],
        total_contatos=total_contatos,
        total_grupos=total_grupos,
        total_campanhas=total_campanhas,
        total_usuarios=total_usuarios
    )


@app.route('/logout')
def logout():
    log = Log(acao='logout', usuario_email=session.get('usuario'), detalhes='Logout realizado')
    db.session.add(log)
    db.session.commit()
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
