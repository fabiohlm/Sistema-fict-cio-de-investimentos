from flask import Flask, session, redirect, url_for, render_template, request
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
from abc import ABC, abstractmethod

app = Flask(__name__)
app.secret_key = '123456'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///minhabase.sqlite3'
db = SQLAlchemy(app)

class ChatGPT(ABC):
  chave = 'chave_do_chatGPT_aqui'
  modelo_inteligencia = 'gpt-3.5-turbo-0125'
  formato_resposta = {"type": "text"}
  conexao = None

  def __init__(self):
    self.conexao = OpenAI(api_key = self.chave)

class ChatRoom:
    def painel_mensagens(self, user, mensagem):
        return f"[{user}]: {mensagem}"

class Consultor(ChatGPT):
    def __init__(self):
        super().__init__()
        self.tipo = "consultor de investimentos competente"
        self.chatroom = None

    def gerar_resposta(self,  pergunta, chatroom):
        questao = self.conexao.chat.completions.create(
                    model = self.modelo_inteligencia,
                    response_format= self.formato_resposta,
                    messages=[
                          {"role": "system", "content": "Atue como "+self.tipo},
                          {"role": "user", "content": "Sabendo que a corretora de investimentos que você trabalha oferece apenas renda fixa, renda variável e tesouro direto como opções de investimento, e que, se a situação do cliente não se encaixar com as opções oferecidas, você deverá indicar a melhor opção fora das oferecidas, deixando claro que a corretora não a oferece, responda de forma breve a seguinte pergunta do cliente, se negando a responder sobre qualquer assunto que não tenha a ver com investimentos: "+pergunta}
                              ]
                     )
        self.chatroom = chatroom
        text = self.chatroom.painel_mensagens('Consultor', questao.choices[0].message.content)
        return text

class Usuario(db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, unique=True)
    senha = db.Column(db.String)
    def __init__(self, nome, senha):
        self.nome = nome
        self.senha = senha
        self.chatroom = None

    def postar_pergunta(self, mensagem, chatroom):
        self.chatroom = chatroom
        text = self.chatroom.painel_mensagens(self.nome, mensagem)
        return text

class Investimento(db.Model):
    __tablename__ = "investimentos"
    id = db.Column(db.Integer, primary_key=True)
    nomeus = db.Column(db.String)
    tipo = db.Column(db.String)
    valor = db.Column(db.Float)
    periodo = db.Column(db.Integer)
    taxa = db.Column(db.Float)
    def __init__(self, nomeus, tipo, valor, periodo, taxa):
        self.tipo = tipo
        self.nomeus = nomeus
        self.valor = float(valor)
        self.periodo = int(periodo)
        self.taxa = float(taxa)

class InvestimentoBuilder:
    def nome(self, val):
        self.nome = val

    def tipo(self, val):
        self.tipo = val

    def valor(self, val):
        self.valor = val

    def periodo(self, val):
        self.periodo = val

    def taxa(self, val):
        self.taxa = val

    def build(self):
        return Investimento(self.nome, self.tipo, self.valor, self.periodo, self.taxa)

class CalcularInvestimento:
    @abstractmethod
    def calcular(valor, taxa, periodo):
        valor = float(valor)
        taxa = float(taxa)
        periodo = int(periodo)
        return valor*(float(1+taxa*0.01)**periodo)

class CalcularProxy:
    def __init__(self):
        self._cache = {}

    def calcularpr(self, val, tax, per):
        if per in self._cache:
            return self._cache[per]
        else:
            resultado = CalcularInvestimento.calcular(val, tax, per)
            self._cache[per] = resultado
            return resultado

@app.route("/usuario", methods=['POST', 'GET'])
def addUsuario():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        user = Usuario(nome, senha)
        db.session.add(user)
        db.session.commit()
    users = Usuario.query.all()
    return render_template('usuario.html', usuarios=users)

@app.route('/')
def index():
    if 'username' in session:
        return 'Logado como {} <br><form action="/empinv"><input type=submit value="Página de Investimentos"></form> <form action ="/logout"><input type="submit" value ="Logout"></form><p><a href="/tabela">Lista de investimentos</a></p>'.format(session['username'])
    return 'Você não está logado <br><form action="/login"><input type=submit value="Fazer login"></form>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = Usuario.query.all()
        for i in users:
            if request.form['username'] in i.nome and request.form['password'] == i.senha:
                session['username'] = request.form['username']
                return redirect(url_for('index'))
                break
        return 'Login Incorreto <br><form action="/login"><input type=submit value="Fazer login"></form>'
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sistema de investimentos</title>
    </head>
    <body>
        <h1>Sistema de investimentos</h1>
        <div>
            <h2>Login</h2>
            <form action="login" method="POST">
                <label for="usuario">Usuário</label>
                <input type="text" name="username" id="username">
                </label><br>
                <label for="password">Senha</label>
                <input type="password" name="password" id="password">
                <br>
                <input type="submit" value="Fazer login">
                <p><a href="/usuario">Cadastro de Usuário</a></p>
            </form>
        </div>

    </body>
    </html> '''

@app.route("/empinv", methods=['POST', 'GET'])
def emprestimosInvestimentos():
    if 'username' not in session:
        return redirect(url_for('index'))
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sistema de investimentos</title>
    </head>
    <body>
        <h1>Sistema de investimentos</h1>
        <div>
            <h2>Investimentos</h2>
            <p><a href="/investimento">Tela de investimentos</a></p>
            <p><a href="/tabela">Lista de investimentos</a></p>
            <p><a href="/consultor">Consultor de investimentos</a></p>
        </div>
    </body>
    </html> '''

@app.route("/investimento", methods=['POST', 'GET'])
def addInvestimento():
    if 'username' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        builder = InvestimentoBuilder()
        builder.nome(session['username'])
        builder.tipo(request.form['tipo'])
        builder.valor(request.form['valor'])
        builder.taxa(request.form['taxa'])
        builder.periodo(request.form['periodo'])
        invest = builder.build()
        backup = invest.salvar()
        db.session.add(invest)
        db.session.add(backup)
        db.session.commit()
        return 'Operação concluída com sucessos <br><form action="/empinv"><input type=submit value="Página de Investimentos"></form> <form action ="/logout"><input type="submit" value ="Logout"></form>'
    return render_template('investimento.html')

@app.route("/tabela", methods=['POST', 'GET'])
def verInvestimento():
    inv = Investimento.query.filter_by(nomeus=session['username']).all()
    return render_template('tabela.html', investimentos=inv)

@app.route("/apagarinv", methods=['POST', 'GET'])
def apagarInvestimento():
    nid = request.form['tipo']
    x = Investimento.query.filter_by(id=nid).first()
    db.session.delete(x)
    db.session.commit()
    return 'Operação concluída com sucessos <br><form action="/tabela"><input type=submit value="Lista de investimentos"></form> <form action ="/logout"><input type="submit" value ="Logout"></form>'

@app.route("/altinv", methods=['POST', 'GET'])
def alterarInvestimento():
    nid = request.form['tipo']
    x = Investimento.query.filter_by(id=nid).first()
    ht1 = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sistema de investimentos</title>
        </head>
        <body>
            <div>
                <h2>Alterar Investimento</h2>
                <form action="/altinve" method="post">

                    '''
    htid = '<label for="idinv">ID </label><input type="text" id="idinv" name="idinv" value = {} readonly><br>'.format(x.id)
    if x.tipo == "tesouro direto":
        ht2 = '''
            Tipo de investimento: <br>
            <input type="radio" id="tipo" name="tipo" value="tesouro direto" checked="checked">
            <label for="tesouro direto">Tesouro Direto</label><br>
            <input type="radio" id="tipo" name="tipo" value="renda fixa">
            <label for="renda fixa">Renda Fixa</label><br>
            <input type="radio" id="tipo" name="tipo" value="renda variavel">
            <label for="renda variavel">Renda Variável</label>
                '''
    elif x.tipo == "renda fixa":
        ht2 = '''
            Tipo de investimento: <br>
            <input type="radio" id="tipo" name="tipo" value="tesouro direto">
            <label for="tesouro direto">Tesouro Direto</label><br>
            <input type="radio" id="tipo" name="tipo" value="renda fixa" checked="checked">
            <label for="renda fixa">Renda Fixa</label><br>
            <input type="radio" id="tipo" name="tipo" value="renda variavel">
            <label for="renda variavel">Renda Variável</label>
                '''
    elif x.tipo == "renda variavel":
        ht2 = '''
            Tipo de investimento: <br>
            <input type="radio" id="tipo" name="tipo" value="tesouro direto">
            <label for="tesouro direto">Tesouro Direto</label><br>
            <input type="radio" id="tipo" name="tipo" value="renda fixa">
            <label for="renda fixa">Renda Fixa</label><br>
            <input type="radio" id="tipo" name="tipo" value="renda variavel" checked="checked">
            <label for="renda variavel">Renda Variável</label>
                '''
    ht3 = '''
        <br>
        <label for="valor">Valor</label>
        '''
    ht4 = '<input type="number" step="0.01" id="valor" name="valor" value = {}><br>'.format(x.valor)

    ht5 = '<label for="taxa">Taxa(%)</label><input type="number" step="0.01" id="taxa" name="taxa" value = {}><br>'.format(x.taxa)

    ht6 = '<label for="periodo">Periodo(meses)</label><input type="number" id="periodo" name="periodo" value = {}><br>'.format(x.periodo)

    ht7 = '''
    <input type="submit" value="Efetuar">
                </form>
                <p><a href="/empinv">Voltar</a></p>
            </div>
        </body>
        </html>
        '''
    ht = ht1+htid+ht2+ht3+ht4+ht5+ht6+ht7
    return ht

@app.route("/altinve", methods=['POST', 'GET'])
def alterarInv():
    x = Investimento.query.filter_by(id=request.form['idinv']).first()
    x.tipo = request.form['tipo']
    x.valor = request.form['valor']
    x.taxa = request.form['taxa']
    x.periodo = request.form['periodo']
    db.session.commit()
    return 'Operação concluída com sucessos <br><form action="/empinv"><input type=submit value="Página de Investimentos"></form> <form action ="/logout"><input type="submit" value ="Logout"></form>'


@app.route("/consultor", methods=['POST', 'GET'])
def perguntarConsultor():
    if request.method == 'POST':
        user = Usuario.query.filter_by(nome=session['username']).first()
        usuario = Usuario(user.nome, user.senha)
        chat = ChatRoom()
        perg = request.form['perg']
        consult = Consultor()
        pergunta = usuario.postar_pergunta(perg, chat)
        resposta = consult.gerar_resposta(perg, chat)
        ht1 = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sistema de investimentos</title>
        </head>
        <body>
            <h1>Sistema de investimentos</h1>
            <div>
                <h2>Consultor de investimentos</h2>
                <form action="/consultor" method="POST" >
                    <label for="perg">Peça ao consultor uma dica de investimento de acordo com sua situação financeira, expectativa de prazo de recebimento e perfil de risco:</label>
                    <br>
                    <input type="text" name="perg" id="perg">
                    <br>
        '''
        ht2 = '<p>{}</p><br>'.format(pergunta)
        htresp = '<p>{}</p><br>'.format(resposta)
        ht3 = '''
            <input type="submit" value="Fazer pergunta">
                    <p><a href="/empinv">Voltar</a></p>
                </form>
            </div>
        </body>
        </html>
        '''
        return ht1+ht2+htresp+ht3
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sistema de investimentos</title>
    </head>
    <body>
        <h1>Sistema de investimentos</h1>
        <div>
            <h2>Consultor de investimentos</h2>
            <form action="/consultor" method="POST">
                <label for="perg">Peça ao consultor uma dica de investimento de acordo com sua situação financeira, expectativa de prazo de recebimento e perfil de risco:</label>
                <br>
                <input type="text" name="perg" id="perg">
                <br>
                <input type="submit" value="Fazer pergunta">
                <p><a href="/empinv">Voltar</a></p>
            </form>
        </div>
    </body>
    </html> '''

@app.route("/calcularinv", methods=['POST', 'GET'])
def calcularInvestimentos():
    nid = request.form['tipo']
    x = Investimento.query.filter_by(id=nid).first()
    if 'username' not in session:
        return redirect(url_for('index'))
    ht1 = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sistema de investimentos</title>
        </head>
        <body>
            <div>
                <h2>Calcular Investimento</h2>
                <form action="/calcularinve" method="post" id="x" name="x">

                    '''
    htid = '<label for="id">ID</label><input type="number" id="id" name="id" value = {} readonly>'.format(x.id)

    ht2 = '<br><label for="valor">Valor</label>'

    ht3 = '<input type="number" step="0.01" id="valor" name="valor" value = {} readonly><br>'.format(x.valor)

    ht4 = '<label for="taxa">Taxa(%)</label><input type="number" step="0.01" id="taxa" name="taxa" value = {} readonly><br>'.format(x.taxa)

    ht5 = '<label for="periodo">Periodo(meses)</label><select name="periodo" id="periodo" form="x">'

    ht6 = ''
    for i in range(x.periodo):
        ht6 += '<option value={}>{}</option>'.format(i+1,i+1)
    ht7 = '''
    </select>
    <input type="submit" value="Efetuar">
                </form>
                <p><a href="/empinv">Voltar</a></p>
            </div>
        </body>
        </html>
        '''
    ht = ht1+htid+ht2+ht3+ht4+ht5+ht6+ht7
    return ht

@app.route("/calcularinve", methods=['POST', 'GET'])
def calcularInvestimento():
    val = request.form['valor']
    tax = request.form['taxa']
    per = request.form['periodo']
    cal = CalcularProxy()
    res = cal.calcularpr(val, tax, per)
    nid = request.form['id']
    x = Investimento.query.filter_by(id=nid).first()
    if 'username' not in session:
        return redirect(url_for('index'))
    ht1 = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sistema de investimentos</title>
        </head>
        <body>
            <div>
                <h2>Calcular Investimento</h2>
                <form action="/calcularinve" method="post" id="x" name="x">

                    '''
    htid = '<label for="id">ID</label><input type="number" id="id" name="id" value = {} readonly>'.format(x.id)

    ht2 = '<br><label for="valor">Valor</label>'

    ht3 = '<input type="number" step="0.01" id="valor" name="valor" value = {} readonly><br>'.format(x.valor)

    ht4 = '<label for="taxa">Taxa(%)</label><input type="number" step="0.01" id="taxa" name="taxa" value = {} readonly><br>'.format(x.taxa)

    ht5 = '<label for="periodo">Periodo(meses)</label><select name="periodo" id="periodo" form="x">'

    ht6 = ''
    for i in range(x.periodo):
        ht6 += '<option value={}>{}</option>'.format(i+1,i+1)

    ht7 = '''
    </select>
    '''
    htres = '<p>Valor resgatado: R${:.2f}</p>'.format(res)
    ht8 ='''<input type="submit" value="Efetuar">
                </form>
                <p><a href="/empinv">Voltar</a></p>
            </div>
        </body>
        </html>
        '''
    ht = ht1+htid+ht2+ht3+ht4+ht5+ht6+ht7+htres+ht8
    return ht

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_error(error):
    return 'Ocorreu um erro <br><form action="/login"><input type=submit value="Página de login"></form>'

if __name__ == "__main__":
    db.create_all()
    app.run()
