from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
import os

# Carrega as variáveis do arquivo .env
load_dotenv()

app = Flask(__name__)

# Chave secreta para gerenciar sessões de login
app.secret_key = os.getenv('SECRET_KEY', 'bbrain-dev-key')

# ─────────────────────────────────────────
# USUÁRIOS DO SISTEMA
# Por enquanto ficam aqui. Depois vamos
# mover para o banco de dados.
# ─────────────────────────────────────────
USUARIOS = {
    "admin@bbrain.com": {
        "senha": "bbrain123",
        "nome": "Admin",
        "perfil": "admin"
    }
}

# ─────────────────────────────────────────
# ROTAS
# ─────────────────────────────────────────

@app.route('/')
def index():
    # Se já está logado, vai pro dashboard
    if 'usuario' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    senha = request.form.get('senha')

    # Verifica se o usuário existe e a senha está correta
    if email in USUARIOS and USUARIOS[email]['senha'] == senha:
        session['usuario'] = email
        session['nome'] = USUARIOS[email]['nome']
        session['perfil'] = USUARIOS[email]['perfil']
        return redirect(url_for('dashboard'))
    
    # Login inválido — volta pra tela de login com erro
    flash('Email ou senha incorretos.')
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    # Protege a rota — só acessa se estiver logado
    if 'usuario' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html', nome=session['nome'])


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ─────────────────────────────────────────
# INICIA O SERVIDOR
# ─────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)
