from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "handball_fantasy_fbd"

# Dados temporários para testar o frontend antes de ligar as queries SQL
MOCK_USERS = [
    {"id_utilizador": 1, "nome": "João Silva", "email": "joao@ua.pt"},
    {"id_utilizador": 2, "nome": "Ana Costa", "email": "ana@ua.pt"},
]

MOCK_CLUBES = [
    {"id_clube": 1, "nome": "THW Kiel", "pais": "Alemanha", "treinador": "Filip Jícha", "pavilhao": "Wunderino Arena", "total_jogadores": 2},
    {"id_clube": 2, "nome": "Füchse Berlin", "pais": "Alemanha", "treinador": "Jaron Siewert", "pavilhao": "Max-Schmeling-Halle", "total_jogadores": 1},
]

MOCK_POSICOES = [
    {"id_posicao": 1, "nome": "Guarda-Redes", "sigla": "GR"},
    {"id_posicao": 2, "nome": "Lateral Direito", "sigla": "LD"},
    {"id_posicao": 3, "nome": "Central", "sigla": "CE"},
]

MOCK_PAISES = [
    {"id_pais": 1, "nome": "Portugal"},
    {"id_pais": 2, "nome": "Alemanha"},
    {"id_pais": 3, "nome": "Dinamarca"},
]

MOCK_JOGADORES = [
    {"id_jogador": 1, "nome": "Mathias Gidsel", "numero_camisola": 19, "id_clube": 2, "clube": "Füchse Berlin", "id_posicao": 2, "posicao": "Lateral Direito", "posicao_sigla": "LD", "id_pais": 3, "pais": "Dinamarca", "total_golos": 48, "total_pontos": 112, "pontos": 112},
    {"id_jogador": 2, "nome": "Domagoj Duvnjak", "numero_camisola": 5, "id_clube": 1, "clube": "THW Kiel", "id_posicao": 3, "posicao": "Central", "posicao_sigla": "CE", "id_pais": 2, "pais": "Alemanha", "total_golos": 22, "total_pontos": 76, "pontos": 76},
    {"id_jogador": 3, "nome": "Andreas Wolff", "numero_camisola": 33, "id_clube": 1, "clube": "THW Kiel", "id_posicao": 1, "posicao": "Guarda-Redes", "posicao_sigla": "GR", "id_pais": 2, "pais": "Alemanha", "total_golos": 1, "total_pontos": 89, "pontos": 89},
]

MOCK_JORNADAS = [{"id_jornada": 1, "nome": "Jornada 1"}, {"id_jornada": 2, "nome": "Jornada 2"}]

MOCK_JOGOS = [
    {"id_jogo": 1, "id_jornada": 1, "nome_jornada": "Jornada 1", "data_hora": "2026-11-10 19:30", "clube_casa": "THW Kiel", "clube_fora": "Füchse Berlin", "golos_casa": 31, "golos_fora": 29, "pavilhao": "Wunderino Arena"},
    {"id_jogo": 2, "id_jornada": 2, "nome_jornada": "Jornada 2", "data_hora": "2026-11-17 20:00", "clube_casa": "Füchse Berlin", "clube_fora": "THW Kiel", "golos_casa": None, "golos_fora": None, "pavilhao": "Max-Schmeling-Halle"},
]

def current_user():
    uid = session.get("user_id")
    return next((u for u in MOCK_USERS if u["id_utilizador"] == uid), None)

@app.route("/")
def index():
    user = current_user()
    minhas_ligas = [{"id_liga": 1, "id_plantel": 1, "nome_liga": "Liga FBD Aveiro", "nome_plantel": "Aveiro HC", "posicao": 1, "pontos": 188}] if user else []
    stats = {"pontos_totais": 188, "melhor_rank": "#1"} if user else None
    return render_template("index.html", utilizador=user, minhas_ligas=minhas_ligas, jogos_jornada=MOCK_JOGOS, stats_resumo=stats)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uid = request.form.get("id_utilizador")
        if uid:
            session["user_id"] = int(uid)
            flash("Sessão iniciada com sucesso!", "success")
            return redirect(url_for("index"))
        flash("Seleciona um utilizador válido.", "error")
    return render_template("login.html", utilizador=current_user(), utilizadores=MOCK_USERS, paises=MOCK_PAISES)

@app.route("/registar", methods=["POST"])
def registar():
    flash("Conta criada com sucesso!", "success")
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("index"))

@app.route("/ligas")
def ligas():
    user = current_user()
    lista = [{"id_liga": 1, "nome": "Liga FBD Aveiro", "descricao": "Competição oficial da UC", "total_participantes": 6, "inscrito": bool(user)}]
    return render_template("ligas.html", utilizador=user, ligas=lista)

@app.route("/ligas/criar", methods=["POST"])
def criar_liga():
    flash("Liga criada!", "success")
    return redirect(url_for("ligas"))

@app.route("/ligas/<int:id_liga>/entrar", methods=["POST"])
def entrar_liga(id_liga):
    flash("Inscrição efetuada na liga!", "success")
    return redirect(url_for("liga_detalhe", id_liga=id_liga))

@app.route("/ligas/<int:id_liga>")
def liga_detalhe(id_liga):
    liga = {"id_liga": id_liga, "nome": "Liga FBD Aveiro", "descricao": "Competição oficial da UC"}
    classificacao = [
        {"id_plantel": 1, "nome_utilizador": "João Silva", "nome_plantel": "Aveiro HC", "pontos_jornada": 94, "pontos_totais": 188},
        {"id_plantel": 2, "nome_utilizador": "Ana Costa", "nome_plantel": "Ria Seven", "pontos_jornada": 81, "pontos_totais": 165},
    ]
    return render_template("liga_detalhe.html", utilizador=current_user(), liga=liga, classificacao=classificacao, jornadas=MOCK_JORNADAS, jornada_selecionada=None, meu_plantel_id=1)

@app.route("/plantel/<int:id_plantel>")
def plantel(id_plantel):
    p_info = {"id_plantel": id_plantel, "id_liga": 1, "nome": "Aveiro HC", "pontos_totais": 188}
    return render_template("plantel.html", utilizador=current_user(), plantel=p_info, jogadores_plantel=MOCK_JOGADORES[:2], mercado_jogadores=MOCK_JOGADORES, clubes=MOCK_CLUBES, posicoes=MOCK_POSICOES, jornadas=MOCK_JORNADAS, modo_leitura=False)

@app.route("/plantel/<int:id_plantel>/renomear", methods=["POST"])
@app.route("/plantel/<int:id_plantel>/adicionar", methods=["POST"])
@app.route("/plantel/<int:id_plantel>/remover", methods=["POST"])
def plantel_acoes(id_plantel):
    flash("Plantel atualizado!", "success")
    return redirect(url_for("plantel", id_plantel=id_plantel))

@app.route("/jogadores")
def jogadores():
    historico = [{"id_jogador": 1, "id_jogo": 1, "descricao_jogo": "THW Kiel 31 - 29 Füchse Berlin", "golos": 9, "defesas": 0, "exclusoes": 1, "pontos": 22}]
    return render_template("jogadores.html", utilizador=current_user(), jogadores=MOCK_JOGADORES, clubes=MOCK_CLUBES, posicoes=MOCK_POSICOES, paises=MOCK_PAISES, historico_jogos=historico)

@app.route("/jogadores/criar", methods=["POST"])
@app.route("/jogadores/<int:id_jogador>/editar", methods=["POST"])
@app.route("/jogadores/<int:id_jogador>/eliminar", methods=["POST"])
def jogadores_acoes(id_jogador=None):
    flash("Operação concluída!", "success")
    return redirect(url_for("jogadores"))

@app.route("/clubes")
def clubes():
    jog_clube = {1: [j for j in MOCK_JOGADORES if j["id_clube"] == 1], 2: [j for j in MOCK_JOGADORES if j["id_clube"] == 2]}
    return render_template("clubes.html", utilizador=current_user(), clubes=MOCK_CLUBES, jogadores_por_clube=jog_clube)

@app.route("/jogos")
def jogos():
    pavilhoes = [{"id_pavilhao": 1, "nome": "Wunderino Arena", "cidade": "Kiel"}]
    arbitros = [{"id_arbitro": 1, "nome": "Duarte Santos"}, {"id_arbitro": 2, "nome": "Ricardo Fonseca"}]
    return render_template("jogos.html", utilizador=current_user(), jornadas=MOCK_JORNADAS, jogos=MOCK_JOGOS, clubes=MOCK_CLUBES, pavilhoes=pavilhoes, arbitros=arbitros)

@app.route("/jogos/criar", methods=["POST"])
def criar_jogo():
    flash("Jogo agendado!", "success")
    return redirect(url_for("jogos"))

@app.route("/jogos/<int:id_jogo>")
def jogo_detalhe(id_jogo):
    jogo = next((j for j in MOCK_JOGOS if j["id_jogo"] == id_jogo), MOCK_JOGOS[0])
    stats_casa = [{"id_jogador": 2, "nome": "Domagoj Duvnjak", "golos": 6, "defesas": 0, "exclusoes": 1, "pontos": 15}]
    stats_fora = [{"id_jogador": 1, "nome": "Mathias Gidsel", "golos": 9, "defesas": 0, "exclusoes": 1, "pontos": 22}]
    return render_template("jogo_detalhe.html", utilizador=current_user(), jogo=jogo, arbitros_jogo=[{"nome": "Duarte Santos"}], stats_casa=stats_casa, stats_fora=stats_fora, jogadores_participantes=MOCK_JOGADORES)

@app.route("/jogos/<int:id_jogo>/estatisticas", methods=["POST"])
def jogo_estatisticas(id_jogo):
    flash("Estatística guardada!", "success")
    return redirect(url_for("jogo_detalhe", id_jogo=id_jogo))

if __name__ == "__main__":
    app.run(debug=True)