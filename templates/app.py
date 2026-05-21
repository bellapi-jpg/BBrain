from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from database import db, Usuario, Log, Contato, Grupo, Campanha
import os
import openpyxl

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'bbrain-dev-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///bbrain.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    if not Usuario.query.first():
        admin = Usuario(nome='Admin', email='admin@bbrain.com', perfil='admin')
        admin.definir_senha('bbrain123')
        db.session.add(admin)
        db.session.commit()
        print('✅ Admin criado!')


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def login_necessario():
    return 'usuario' not in session


# ─────────────────────────────────────────
# LOGIN / LOGOUT
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
        log = Log(acao='login', usuario_email=usuario.email, detalhes='Login realizado')
        db.session.add(log)
        db.session.commit()
        return redirect(url_for('dashboard'))
    flash('Email ou senha incorretos.')
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    log = Log(acao='logout', usuario_email=session.get('usuario'), detalhes='Logout realizado')
    db.session.add(log)
    db.session.commit()
    session.clear()
    return redirect(url_for('index'))


# ─────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────
@app.route('/dashboard')
def dashboard():
    if login_necessario():
        return redirect(url_for('index'))

    total_contatos = Contato.query.count()
    total_grupos = Grupo.query.filter_by(ativo=True).count()
    total_campanhas = Campanha.query.filter_by(status='enviada').count()
    total_usuarios = Usuario.query.filter_by(ativo=True).count()

    # Contatos por bairro para o gráfico
    from sqlalchemy import func
    bairros = db.session.query(
        Contato.bairro,
        func.count(Contato.id).label('total')
    ).filter(
        Contato.bairro != None,
        Contato.bairro != ''
    ).group_by(Contato.bairro).order_by(func.count(Contato.id).desc()).limit(10).all()

    bairros_labels = [b.bairro for b in bairros]
    bairros_valores = [b.total for b in bairros]

    return render_template('dashboard.html',
        nome=session['nome'],
        total_contatos=total_contatos,
        total_grupos=total_grupos,
        total_campanhas=total_campanhas,
        total_usuarios=total_usuarios,
        bairros_labels=bairros_labels,
        bairros_valores=bairros_valores
    )


# ─────────────────────────────────────────
# CONTATOS
# ─────────────────────────────────────────
@app.route('/contatos')
def contatos():
    if login_necessario():
        return redirect(url_for('index'))

    bairro_filtro = request.args.get('bairro', '')
    busca = request.args.get('busca', '')

    query = Contato.query
    if bairro_filtro:
        query = query.filter_by(bairro=bairro_filtro)
    if busca:
        query = query.filter(Contato.nome.ilike(f'%{busca}%'))

    lista = query.order_by(Contato.nome).all()

    # Lista de bairros únicos para o filtro
    from sqlalchemy import func
    bairros = db.session.query(Contato.bairro).filter(
        Contato.bairro != None,
        Contato.bairro != ''
    ).distinct().order_by(Contato.bairro).all()
    bairros = [b.bairro for b in bairros]

    return render_template('contatos.html',
        contatos=lista,
        bairros=bairros,
        bairro_filtro=bairro_filtro,
        busca=busca,
        total=len(lista)
    )


@app.route('/contatos/importar', methods=['POST'])
def importar_contatos():
    if login_necessario():
        return redirect(url_for('index'))

    arquivo = request.files.get('planilha')
    if not arquivo:
        flash('Nenhum arquivo enviado.')
        return redirect(url_for('contatos'))

    try:
        wb = openpyxl.load_workbook(arquivo)
        ws = wb.active

        importados = 0
        ignorados = 0

        for row in ws.iter_rows(min_row=2, values_only=True):
            nome = str(row[0]).strip() if row[0] else None
            email = str(row[1]).strip() if row[1] else None
            telefone = str(row[2]).strip() if row[2] else None
            cidade = str(row[3]).strip() if row[3] else None
            bairro = str(row[4]).strip() if row[4] else None
            como_conheceu = str(row[5]).strip() if row[5] else None

            if not nome:
                ignorados += 1
                continue

            # Evita duplicatas por telefone
            if telefone and Contato.query.filter_by(telefone=telefone).first():
                ignorados += 1
                continue

            contato = Contato(
                nome=nome,
                email=email,
                telefone=telefone,
                cidade=cidade,
                bairro=bairro,
                como_conheceu=como_conheceu
            )
            db.session.add(contato)
            importados += 1

        db.session.commit()

        log = Log(
            acao='importar_contatos',
            usuario_email=session.get('usuario'),
            detalhes=f'{importados} importados, {ignorados} ignorados'
        )
        db.session.add(log)
        db.session.commit()

        flash(f'✅ {importados} contatos importados! {ignorados} ignorados (duplicatas ou sem nome).')

    except Exception as e:
        flash(f'❌ Erro ao processar planilha: {str(e)}')

    return redirect(url_for('contatos'))


if __name__ == '__main__':
    app.run(debug=True)
