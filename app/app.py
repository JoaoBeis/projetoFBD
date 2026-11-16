"""
Aplicação Web Flask — Handball Fantasy League
Alinhada com o esquema relacional e dados DML de APFE_FINAL_132982_133155/sql/04_db_init.sql

Todas as tabelas do esquema físico estão representadas em estruturas Python MOCK
carregadas diretamente a partir do ficheiro SQL de inicialização:
- utilizador, plantel, pais, posicao, clube, pavilhao, arbitro,
  treinador, pessoa, jogador, seleciona, liga, participa_liga,
  jornada, participa_jornada, jogo, apita, participa_jogo.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from mock_data import (
    MOCK_USERS,
    MOCK_PLANTEIS,
    MOCK_PAISES,
    MOCK_POSICOES,
    MOCK_CLUBES,
    MOCK_PAVILHOES,
    MOCK_ARBITROS,
    MOCK_JOGADORES,
    MOCK_SELECIONA,
    MOCK_LIGAS,
    MOCK_PARTICIPA_LIGA,
    MOCK_JORNADAS,
    MOCK_PARTICIPA_JORNADA,
    MOCK_JOGOS,
    MOCK_APITA,
    MOCK_PARTICIPA_JOGO,
    HISTORICO_JOGOS,
)

app = Flask(__name__)
app.secret_key = "handball_fantasy_fbd"

# ==============================================================================
# FUNÇÕES AUXILIARES DE SESSÃO E ENTIDADES
# ==============================================================================

def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return next((u for u in MOCK_USERS if u["id_utilizador"] == uid), None)


def get_user_plantel(user_id):
    """
    Garante a regra de integridade do DDL:
    Cada utilizador gere exatamente 1 plantel (UNIQUE(id_utilizador)).
    """
    if user_id not in MOCK_PLANTEIS:
        user = next((u for u in MOCK_USERS if u["id_utilizador"] == user_id), None)
        username = user["username"] if user else f"user_{user_id}"
        new_id = max([p["id_plantel"] for p in MOCK_PLANTEIS.values()], default=0) + 1
        MOCK_PLANTEIS[user_id] = {
            "id_plantel": new_id,
            "nome_plantel": f"Plantel de {username}",
            "orcamento": 100000000.0,
            "pontos_acumulados": 0.0,
            "id_utilizador": user_id,
            "username": username,
        }
        MOCK_SELECIONA.setdefault(new_id, [])
    return MOCK_PLANTEIS[user_id]


def get_plantel_by_id(id_plantel):
    for p in MOCK_PLANTEIS.values():
        if p["id_plantel"] == id_plantel:
            return p
    return None


def build_jogadores_plantel(id_plantel):
    """
    Cruza a tabela 'seleciona' com a tabela 'jogador' e 'pessoa'
    para construir o plantel com estado de titular, capitão e preço de compra.
    """
    selecionados = MOCK_SELECIONA.get(id_plantel, [])
    result = []
    for s in selecionados:
        jog = next((j for j in MOCK_JOGADORES if j["id_jogador"] == s["id_jogador"]), None)
        if jog:
            item = dict(jog)
            item["preco_compra"] = s["preco_compra"]
            item["e_titular"] = s["e_titular"]
            item["e_capitao"] = s["e_capitao"]
            result.append(item)
    return result


# ==============================================================================
# ROTAS FLASK — PÁGINA INICIAL E AUTENTICAÇÃO
# ==============================================================================

@app.route("/")
def index():
    user = current_user()
    minhas_ligas = []
    stats = None

    if user:
        p = get_user_plantel(user["id_utilizador"])
        stats = {"pontos_totais": p["pontos_acumulados"], "melhor_rank": "#1"}
        # Cruzar participa_liga com MOCK_LIGAS
        inscricoes = [pl["id_liga"] for pl in MOCK_PARTICIPA_LIGA if pl["id_plantel"] == p["id_plantel"]]
        for liga in MOCK_LIGAS:
            if liga["id_liga"] in inscricoes:
                part_ids = [pl["id_plantel"] for pl in MOCK_PARTICIPA_LIGA if pl["id_liga"] == liga["id_liga"]]
                rank_list = sorted(
                    [get_plantel_by_id(pid) for pid in part_ids if get_plantel_by_id(pid)],
                    key=lambda x: x["pontos_acumulados"],
                    reverse=True,
                )
                pos = next((i + 1 for i, item in enumerate(rank_list) if item["id_plantel"] == p["id_plantel"]), 1)
                minhas_ligas.append({
                    "id_liga": liga["id_liga"],
                    "nome_liga": liga["nome"],
                    "posicao": pos,
                    "pontos": int(p["pontos_acumulados"]),
                })

    # Jogos da jornada atual (Jornada 1) para o resumo na dashboard
    jogos_jornada = [j for j in MOCK_JOGOS if j["numero_jornada"] == 1]
    if not jogos_jornada:
        jogos_jornada = MOCK_JOGOS[:9]

    return render_template(
        "index.html",
        utilizador=user,
        minhas_ligas=minhas_ligas,
        jogos_jornada=jogos_jornada,
        stats_resumo=stats,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uid = request.form.get("id_utilizador")
        username_ou_email = request.form.get("username_ou_email", "").strip()

        if uid:
            session["user_id"] = int(uid)
            flash("Sessão iniciada com sucesso!", "success")
            return redirect(url_for("meu_plantel"))

        if username_ou_email:
            matched = next(
                (u for u in MOCK_USERS if u["username"].lower() == username_ou_email.lower() or u["email"].lower() == username_ou_email.lower()),
                None,
            )
            if matched:
                session["user_id"] = matched["id_utilizador"]
                flash(f"Bem-vindo, {matched['username']}!", "success")
                return redirect(url_for("meu_plantel"))
            else:
                flash("Credenciais inválidas. Tenta novamente.", "error")
        else:
            flash("Indica o utilizador ou email.", "error")

    return render_template(
        "login.html",
        utilizador=current_user(),
        utilizadores=MOCK_USERS,
        paises=MOCK_PAISES,
    )


@app.route("/registar", methods=["POST"])
def registar():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    nome_plantel = request.form.get("nome_plantel", "").strip()

    if not username or not email or not password or not nome_plantel:
        flash("Todos os campos são obrigatórios.", "error")
        return redirect(url_for("login"))

    # Verificar unicidade (username, email)
    if any(u["username"].lower() == username.lower() for u in MOCK_USERS):
        flash("Esse username já está registado.", "error")
        return redirect(url_for("login"))
    if any(u["email"].lower() == email.lower() for u in MOCK_USERS):
        flash("Esse email já se encontra em uso.", "error")
        return redirect(url_for("login"))

    new_uid = max([u["id_utilizador"] for u in MOCK_USERS], default=0) + 1
    new_user = {
        "id_utilizador": new_uid,
        "username": username,
        "email": email,
        "password_hash": "hash_" + password,
    }
    MOCK_USERS.append(new_user)

    # Criação do plantel único associado ao utilizador (tabela plantel)
    new_plantel_id = max([p["id_plantel"] for p in MOCK_PLANTEIS.values()], default=0) + 1
    MOCK_PLANTEIS[new_uid] = {
        "id_plantel": new_plantel_id,
        "nome_plantel": nome_plantel,
        "orcamento": 100000000.0,
        "pontos_acumulados": 0.0,
        "id_utilizador": new_uid,
        "username": username,
    }
    MOCK_SELECIONA[new_plantel_id] = []

    # Inscrição automática na liga pública principal (id_liga 1)
    MOCK_PARTICIPA_LIGA.append({"id_plantel": new_plantel_id, "id_liga": 1})
    if MOCK_LIGAS:
        MOCK_LIGAS[0]["total_participantes"] = sum(1 for pl in MOCK_PARTICIPA_LIGA if pl["id_liga"] == 1)

    session["user_id"] = new_uid
    flash(f"Conta e Plantel '{nome_plantel}' criados com sucesso!", "success")
    return redirect(url_for("meu_plantel"))


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Sessão terminada.", "success")
    return redirect(url_for("index"))


# ==============================================================================
# ROTAS DO PLANTEL (1 UTILIZADOR <-> 1 PLANTEL ÚNICO)
# ==============================================================================

@app.route("/meu-plantel")
def meu_plantel():
    user = current_user()
    if not user:
        flash("Precisas de iniciar sessão para acederes ao teu plantel.", "error")
        return redirect(url_for("login"))

    p = get_user_plantel(user["id_utilizador"])
    jogadores_convocados = build_jogadores_plantel(p["id_plantel"])
    ids_selecionados = [j["id_jogador"] for j in jogadores_convocados]
    mercado = [j for j in MOCK_JOGADORES if j["id_jogador"] not in ids_selecionados]

    return render_template(
        "plantel.html",
        utilizador=user,
        plantel=p,
        jogadores_plantel=jogadores_convocados,
        mercado_jogadores=mercado,
        clubes=MOCK_CLUBES,
        posicoes=MOCK_POSICOES,
        modo_leitura=False,
    )


@app.route("/plantel/<int:id_plantel>")
def plantel_detalhe(id_plantel):
    user = current_user()
    p = get_plantel_by_id(id_plantel)
    if not p:
        flash("Plantel não encontrado.", "error")
        return redirect(url_for("index"))

    # Se for o próprio plantel do utilizador com sessão, redireciona para a gestão ativa
    if user and p["id_utilizador"] == user["id_utilizador"]:
        return redirect(url_for("meu_plantel"))

    # Modo de observação (apenas leitura) para plantéis adversários
    jogadores_convocados = build_jogadores_plantel(p["id_plantel"])
    return render_template(
        "plantel.html",
        utilizador=user,
        plantel=p,
        jogadores_plantel=jogadores_convocados,
        mercado_jogadores=[],
        clubes=MOCK_CLUBES,
        posicoes=MOCK_POSICOES,
        modo_leitura=True,
    )


@app.route("/meu-plantel/renomear", methods=["POST"])
@app.route("/plantel/<int:id_plantel>/renomear", methods=["POST"])
def renomear_plantel(id_plantel=None):
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    p = get_user_plantel(user["id_utilizador"])
    novo_nome = request.form.get("nome_plantel", "").strip() or request.form.get("nome", "").strip()
    if novo_nome:
        p["nome_plantel"] = novo_nome
        flash(f"Nome do plantel atualizado para '{novo_nome}'!", "success")
    return redirect(url_for("meu_plantel"))


@app.route("/meu-plantel/adicionar", methods=["POST"])
@app.route("/plantel/<int:id_plantel>/adicionar", methods=["POST"])
def adicionar_jogador_plantel(id_plantel=None):
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    p = get_user_plantel(user["id_utilizador"])
    pid = p["id_plantel"]

    id_jogador = int(request.form.get("id_jogador", 0))
    jog = next((j for j in MOCK_JOGADORES if j["id_jogador"] == id_jogador), None)
    if not jog:
        flash("Jogador não encontrado.", "error")
        return redirect(url_for("meu_plantel"))

    squad = MOCK_SELECIONA.setdefault(pid, [])
    if len(squad) >= 14:
        flash("O plantel já atingiu o limite regulamentar de 14 jogadores.", "error")
        return redirect(url_for("meu_plantel"))

    if any(s["id_jogador"] == id_jogador for s in squad):
        flash("Este jogador já se encontra no teu plantel.", "error")
        return redirect(url_for("meu_plantel"))

    preco = jog["valor_mercado"]
    if p["orcamento"] < preco:
        flash(f"Orçamento insuficiente! Necessitas de {preco:,.2f} € e tens apenas {p['orcamento']:,.2f} €.", "error")
        return redirect(url_for("meu_plantel"))

    p["orcamento"] -= preco
    squad.append({
        "id_jogador": id_jogador,
        "e_titular": len(squad) < 7,
        "e_capitao": False,
        "preco_compra": preco,
    })
    flash(f"{jog['primeiro_nome']} {jog['apelido']} contratado com sucesso!", "success")
    return redirect(url_for("meu_plantel"))


@app.route("/meu-plantel/remover", methods=["POST"])
@app.route("/plantel/<int:id_plantel>/remover", methods=["POST"])
def remover_jogador_plantel(id_plantel=None):
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    p = get_user_plantel(user["id_utilizador"])
    pid = p["id_plantel"]

    id_jogador = int(request.form.get("id_jogador", 0))
    squad = MOCK_SELECIONA.get(pid, [])
    item = next((s for s in squad if s["id_jogador"] == id_jogador), None)

    if item:
        p["orcamento"] += item["preco_compra"]
        MOCK_SELECIONA[pid] = [s for s in squad if s["id_jogador"] != id_jogador]
        flash("Jogador vendido! O valor de compra foi creditado de volta ao teu orçamento.", "success")
    else:
        flash("Jogador não encontrado no plantel.", "error")

    return redirect(url_for("meu_plantel"))


@app.route("/meu-plantel/toggle-titular", methods=["POST"])
def toggle_titular():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    p = get_user_plantel(user["id_utilizador"])
    id_jogador = int(request.form.get("id_jogador", 0))

    squad = MOCK_SELECIONA.get(p["id_plantel"], [])
    for s in squad:
        if s["id_jogador"] == id_jogador:
            s["e_titular"] = not s["e_titular"]
            break
    return redirect(url_for("meu_plantel"))


@app.route("/meu-plantel/toggle-capitao", methods=["POST"])
def toggle_capitao():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    p = get_user_plantel(user["id_utilizador"])
    id_jogador = int(request.form.get("id_jogador", 0))

    squad = MOCK_SELECIONA.get(p["id_plantel"], [])
    for s in squad:
        if s["id_jogador"] == id_jogador:
            s["e_capitao"] = not s["e_capitao"]
        else:
            s["e_capitao"] = False  # Apenas 1 capitão por equipa
    return redirect(url_for("meu_plantel"))


# ==============================================================================
# ROTAS DE LIGAS (tabela liga e participa_liga)
# ==============================================================================

@app.route("/ligas")
def ligas():
    user = current_user()
    user_pid = get_user_plantel(user["id_utilizador"])["id_plantel"] if user else None

    # Preparar lista de ligas enriquecida com estado de inscrição
    ligas_view = []
    for liga in MOCK_LIGAS:
        inscrito = any(pl["id_liga"] == liga["id_liga"] and pl["id_plantel"] == user_pid for pl in MOCK_PARTICIPA_LIGA) if user_pid else False
        total = sum(1 for pl in MOCK_PARTICIPA_LIGA if pl["id_liga"] == liga["id_liga"])
        item = dict(liga)
        item["inscrito"] = inscrito
        item["total_participantes"] = total
        ligas_view.append(item)

    return render_template(
        "ligas.html",
        utilizador=user,
        ligas=ligas_view,
        paises=MOCK_PAISES,
    )


@app.route("/ligas/criar", methods=["POST"])
def criar_liga():
    user = current_user()
    if not user:
        flash("Inicia sessão para criares uma liga.", "error")
        return redirect(url_for("login"))

    nome = request.form.get("nome", "").strip()
    e_privada = request.form.get("e_privada") in ("1", "true", "True")
    codigo_acesso = request.form.get("codigo_acesso", "").strip() if e_privada else None
    nome_pais = request.form.get("nome_pais", "").strip() or None

    if not nome:
        flash("O nome da liga é obrigatório.", "error")
        return redirect(url_for("ligas"))

    new_id = max([l["id_liga"] for l in MOCK_LIGAS], default=0) + 1
    nova_liga = {
        "id_liga": new_id,
        "nome": nome,
        "codigo_acesso": codigo_acesso,
        "e_privada": e_privada,
        "nome_pais": nome_pais,
        "id_utilizador": user["id_utilizador"],
        "total_participantes": 1,
    }
    MOCK_LIGAS.append(nova_liga)

    # Inscrição automática do plantel do criador da liga
    p = get_user_plantel(user["id_utilizador"])
    MOCK_PARTICIPA_LIGA.append({"id_plantel": p["id_plantel"], "id_liga": new_id})

    flash(f"Liga '{nome}' criada com sucesso! O teu plantel foi inscrito automaticamente.", "success")
    return redirect(url_for("liga_detalhe", id_liga=new_id))


@app.route("/ligas/<int:id_liga>/entrar", methods=["POST"])
def entrar_liga(id_liga):
    user = current_user()
    if not user:
        flash("Inicia sessão para aderir a esta liga.", "error")
        return redirect(url_for("login"))

    liga = next((l for l in MOCK_LIGAS if l["id_liga"] == id_liga), None)
    if not liga:
        flash("Liga não encontrada.", "error")
        return redirect(url_for("ligas"))

    p = get_user_plantel(user["id_utilizador"])
    ja_inscrito = any(pl["id_liga"] == id_liga and pl["id_plantel"] == p["id_plantel"] for pl in MOCK_PARTICIPA_LIGA)
    if ja_inscrito:
        flash("O teu plantel já está inscrito nesta liga.", "error")
        return redirect(url_for("liga_detalhe", id_liga=id_liga))

    if liga["e_privada"]:
        cod_submetido = request.form.get("codigo_acesso", "").strip()
        if cod_submetido != (liga["codigo_acesso"] or ""):
            flash("Código de acesso incorreto para esta liga privada.", "error")
            return redirect(url_for("ligas"))

    MOCK_PARTICIPA_LIGA.append({"id_plantel": p["id_plantel"], "id_liga": id_liga})
    flash(f"Inscrição confirmada na liga '{liga['nome']}'!", "success")
    return redirect(url_for("liga_detalhe", id_liga=id_liga))


@app.route("/ligas/<int:id_liga>")
def liga_detalhe(id_liga):
    liga = next((l for l in MOCK_LIGAS if l["id_liga"] == id_liga), MOCK_LIGAS[0])
    jornada_req = request.args.get("jornada")
    jornada_sel = int(jornada_req) if jornada_req and jornada_req.isdigit() else None

    # Participantes da liga via participa_liga
    participantes_ids = [pl["id_plantel"] for pl in MOCK_PARTICIPA_LIGA if pl["id_liga"] == id_liga]
    classificacao = []
    for pid in participantes_ids:
        pl_obj = get_plantel_by_id(pid)
        if pl_obj:
            if jornada_sel:
                pj = next((item for item in MOCK_PARTICIPA_JORNADA if item["id_plantel"] == pid and item["id_jornada"] == jornada_sel), None)
                pts_j = pj["pontos_jornada"] if pj else 0.0
            else:
                pj_last = next((item for item in MOCK_PARTICIPA_JORNADA if item["id_plantel"] == pid and item["id_jornada"] == 5), None)
                pts_j = pj_last["pontos_jornada"] if pj_last else 0.0

            classificacao.append({
                "id_plantel": pl_obj["id_plantel"],
                "username": pl_obj["username"],
                "nome_plantel": pl_obj["nome_plantel"],
                "pontos_jornada": pts_j,
                "pontos_totais": pl_obj["pontos_acumulados"],
            })

    classificacao.sort(key=lambda x: x["pontos_totais"], reverse=True)

    jornadas_liga = [j for j in MOCK_JORNADAS if j["id_liga"] == id_liga]
    if not jornadas_liga:
        jornadas_liga = MOCK_JORNADAS

    return render_template(
        "liga_detalhe.html",
        utilizador=current_user(),
        liga=liga,
        classificacao=classificacao,
        jornadas=jornadas_liga,
        jornada_selecionada=jornada_sel,
    )


# ==============================================================================
# ROTAS DE JOGADORES (tabela pessoa e jogador)
# ==============================================================================

@app.route("/jogadores")
def jogadores():
    return render_template(
        "jogadores.html",
        utilizador=current_user(),
        jogadores=MOCK_JOGADORES,
        clubes=MOCK_CLUBES,
        posicoes=MOCK_POSICOES,
        paises=MOCK_PAISES,
        historico_jogos=HISTORICO_JOGOS,
    )


@app.route("/jogadores/criar", methods=["POST"])
def criar_jogador():
    primeiro_nome = request.form.get("primeiro_nome", "").strip()
    apelido = request.form.get("apelido", "").strip()
    data_nasc = request.form.get("data_nasc", "").strip()
    nome_pais = request.form.get("nome_pais", "").strip()
    id_clube = int(request.form.get("id_clube", 1))
    id_posicao = int(request.form.get("id_posicao", 1))
    altura = int(request.form.get("altura")) if request.form.get("altura") else None
    peso = float(request.form.get("peso")) if request.form.get("peso") else None
    valor_mercado = float(request.form.get("valor_mercado", 0))

    clube = next((c for c in MOCK_CLUBES if c["id_clube"] == id_clube), MOCK_CLUBES[0])
    posicao = next((p for p in MOCK_POSICOES if p["id_posicao"] == id_posicao), MOCK_POSICOES[0])

    new_id = max([j["id_jogador"] for j in MOCK_JOGADORES], default=0) + 1
    MOCK_JOGADORES.append({
        "id_jogador": new_id,
        "primeiro_nome": primeiro_nome,
        "apelido": apelido,
        "data_nasc": data_nasc,
        "altura": altura,
        "peso": peso,
        "valor_mercado": valor_mercado,
        "nome_pais": nome_pais,
        "id_clube": id_clube,
        "clube_nome": clube["nome"],
        "id_posicao": id_posicao,
        "posicao_nome": posicao["nome"],
        "posicao_sigla": posicao["sigla"],
        "total_golos": 0,
        "total_pontos": 0.0,
    })

    flash(f"Jogador {primeiro_nome} {apelido} registado com sucesso!", "success")
    return redirect(url_for("jogadores"))


@app.route("/jogadores/<int:id_jogador>/editar", methods=["POST"])
def editar_jogador(id_jogador):
    jog = next((j for j in MOCK_JOGADORES if j["id_jogador"] == id_jogador), None)
    if jog:
        jog["primeiro_nome"] = request.form.get("primeiro_nome", jog["primeiro_nome"]).strip()
        jog["apelido"] = request.form.get("apelido", jog["apelido"]).strip()
        jog["data_nasc"] = request.form.get("data_nasc", jog["data_nasc"]).strip()
        jog["nome_pais"] = request.form.get("nome_pais", jog["nome_pais"]).strip()

        id_clube = int(request.form.get("id_clube", jog["id_clube"]))
        id_posicao = int(request.form.get("id_posicao", jog["id_posicao"]))
        jog["id_clube"] = id_clube
        jog["id_posicao"] = id_posicao

        clube = next((c for c in MOCK_CLUBES if c["id_clube"] == id_clube), None)
        posicao = next((p for p in MOCK_POSICOES if p["id_posicao"] == id_posicao), None)
        if clube:
            jog["clube_nome"] = clube["nome"]
        if posicao:
            jog["posicao_nome"] = posicao["nome"]
            jog["posicao_sigla"] = posicao["sigla"]

        jog["altura"] = int(request.form.get("altura")) if request.form.get("altura") else None
        jog["peso"] = float(request.form.get("peso")) if request.form.get("peso") else None
        jog["valor_mercado"] = float(request.form.get("valor_mercado", jog["valor_mercado"]))

        flash(f"Dados de {jog['primeiro_nome']} {jog['apelido']} atualizados!", "success")
    return redirect(url_for("jogadores"))


@app.route("/jogadores/<int:id_jogador>/eliminar", methods=["POST"])
def eliminar_jogador(id_jogador):
    global MOCK_JOGADORES
    jog = next((j for j in MOCK_JOGADORES if j["id_jogador"] == id_jogador), None)
    nome = f"{jog['primeiro_nome']} {jog['apelido']}" if jog else "Jogador"
    MOCK_JOGADORES = [j for j in MOCK_JOGADORES if j["id_jogador"] != id_jogador]
    # CASCADE nos selecionas
    for squad in MOCK_SELECIONA.values():
        squad[:] = [s for s in squad if s["id_jogador"] != id_jogador]
    flash(f"Registo de {nome} eliminado com sucesso (CASCADE).", "success")
    return redirect(url_for("jogadores"))


# ==============================================================================
# ROTAS DE CLUBES (tabela clube e treinador)
# ==============================================================================

@app.route("/clubes")
def clubes():
    jogadores_por_clube = {}
    for c in MOCK_CLUBES:
        jogadores_por_clube[c["id_clube"]] = [j for j in MOCK_JOGADORES if j["id_clube"] == c["id_clube"]]

    return render_template(
        "clubes.html",
        utilizador=current_user(),
        clubes=MOCK_CLUBES,
        jogadores_por_clube=jogadores_por_clube,
    )


# ==============================================================================
# ROTAS DE JOGOS E PARTICIPAÇÃO (tabela jogo, jornada, pavilhao, participa_jogo)
# ==============================================================================

@app.route("/jogos")
def jogos():
    return render_template(
        "jogos.html",
        utilizador=current_user(),
        jornadas=MOCK_JORNADAS,
        jogos=MOCK_JOGOS,
        clubes=MOCK_CLUBES,
        pavilhoes=MOCK_PAVILHOES,
        arbitros=MOCK_ARBITROS,
    )


@app.route("/jogos/criar", methods=["POST"])
def criar_jogo():
    id_jornada = int(request.form.get("id_jornada", 1))
    data_hora = request.form.get("data_hora", "").replace("T", " ")
    id_clube_casa = int(request.form.get("id_clube_casa", 1))
    id_clube_fora = int(request.form.get("id_clube_fora", 2))
    id_pavilhao = int(request.form.get("id_pavilhao", 1))

    if id_clube_casa == id_clube_fora:
        flash("A equipa da casa e a equipa visitante não podem ser o mesmo clube (CONSTRAINT JOGO_CLUBES_DIFERENTES_CK).", "error")
        return redirect(url_for("jogos"))

    clube_casa = next((c for c in MOCK_CLUBES if c["id_clube"] == id_clube_casa), MOCK_CLUBES[0])
    clube_fora = next((c for c in MOCK_CLUBES if c["id_clube"] == id_clube_fora), MOCK_CLUBES[1])
    pavilhao = next((p for p in MOCK_PAVILHOES if p["id_pavilhao"] == id_pavilhao), MOCK_PAVILHOES[0])
    jornada = next((j for j in MOCK_JORNADAS if j["id_jornada"] == id_jornada), MOCK_JORNADAS[0])

    new_id = max([j["id_jogo"] for j in MOCK_JOGOS], default=0) + 1
    MOCK_JOGOS.append({
        "id_jogo": new_id,
        "id_jornada": id_jornada,
        "numero_jornada": jornada["numero_jornada"],
        "nome_jornada": f"Jornada {jornada['numero_jornada']}",
        "data_hora": data_hora,
        "clube_casa": clube_casa["nome"],
        "id_clube_casa": id_clube_casa,
        "clube_fora": clube_fora["nome"],
        "id_clube_fora": id_clube_fora,
        "golos_casa": None,
        "golos_fora": None,
        "id_pavilhao": id_pavilhao,
        "pavilhao": f"{pavilhao['nome']} ({pavilhao['localidade']})",
    })

    flash("Jogo agendado com sucesso!", "success")
    return redirect(url_for("jogos"))


@app.route("/jogos/<int:id_jogo>")
def jogo_detalhe(id_jogo):
    jogo = next((j for j in MOCK_JOGOS if j["id_jogo"] == id_jogo), MOCK_JOGOS[0])

    stats_casa = [s for s in MOCK_PARTICIPA_JOGO if s["id_jogo"] == id_jogo and s.get("id_clube") == jogo["id_clube_casa"]]
    stats_fora = [s for s in MOCK_PARTICIPA_JOGO if s["id_jogo"] == id_jogo and s.get("id_clube") == jogo["id_clube_fora"]]

    jogadores_participantes = [
        j for j in MOCK_JOGADORES
        if j["id_clube"] in (jogo["id_clube_casa"], jogo["id_clube_fora"])
    ]

    # Árbitros associados a este jogo específico via tabela apita
    arbitros_ids = [a["id_arbitro"] for a in MOCK_APITA if a["id_jogo"] == id_jogo]
    arbitros_jogo = [a for a in MOCK_ARBITROS if a["id_arbitro"] in arbitros_ids]
    if not arbitros_jogo:
        arbitros_jogo = MOCK_ARBITROS[:2]

    return render_template(
        "jogo_detalhe.html",
        utilizador=current_user(),
        jogo=jogo,
        arbitros_jogo=arbitros_jogo,
        stats_casa=stats_casa,
        stats_fora=stats_fora,
        jogadores_participantes=jogadores_participantes,
    )


@app.route("/jogos/<int:id_jogo>/estatisticas", methods=["POST"])
def jogo_estatisticas(id_jogo):
    id_jogador = int(request.form.get("id_jogador", 0))
    golos = int(request.form.get("golos", 0))
    assistencias = int(request.form.get("assistencias", 0))
    remates_falhados = int(request.form.get("remates_falhados", 0))
    exclusoes_2min = int(request.form.get("exclusoes_2min", 0))
    cartoes_vermelhos = int(request.form.get("cartoes_vermelhos", 0))
    cartoes_azuis = int(request.form.get("cartoes_azuis", 0))
    defesas_gr = int(request.form.get("defesas_gr", 0))
    hpi = float(request.form.get("hpi", 0.0))
    pontos_obtidos = float(request.form.get("pontos_obtidos", 0.0))

    jog = next((j for j in MOCK_JOGADORES if j["id_jogador"] == id_jogador), None)
    if not jog:
        flash("Jogador não encontrado.", "error")
        return redirect(url_for("jogo_detalhe", id_jogo=id_jogo))

    # Atualizar ou inserir em MOCK_PARTICIPA_JOGO
    entry = next((s for s in MOCK_PARTICIPA_JOGO if s["id_jogo"] == id_jogo and s["id_jogador"] == id_jogador), None)
    if entry:
        entry.update({
            "golos": golos,
            "assistencias": assistencias,
            "remates_falhados": remates_falhados,
            "exclusoes_2min": exclusoes_2min,
            "cartoes_vermelhos": cartoes_vermelhos,
            "cartoes_azuis": cartoes_azuis,
            "defesas_gr": defesas_gr,
            "hpi": hpi,
            "pontos_obtidos": pontos_obtidos,
        })
    else:
        MOCK_PARTICIPA_JOGO.append({
            "id_jogador": id_jogador,
            "nome": f"{jog['primeiro_nome']} {jog['apelido']}",
            "id_jogo": id_jogo,
            "id_clube": jog["id_clube"],
            "golos": golos,
            "assistencias": assistencias,
            "remates_falhados": remates_falhados,
            "exclusoes_2min": exclusoes_2min,
            "cartoes_vermelhos": cartoes_vermelhos,
            "cartoes_azuis": cartoes_azuis,
            "defesas_gr": defesas_gr,
            "hpi": hpi,
            "pontos_obtidos": pontos_obtidos,
        })

    # Recalcular totais consolidados do jogador
    all_player_pj = [s for s in MOCK_PARTICIPA_JOGO if s["id_jogador"] == id_jogador]
    jog["total_golos"] = sum(s.get("golos", 0) for s in all_player_pj)
    jog["total_pontos"] = round(sum(s.get("pontos_obtidos", 0.0) for s in all_player_pj), 1)

    flash(f"Estatística de {jog['primeiro_nome']} {jog['apelido']} gravada com sucesso em participa_jogo!", "success")
    return redirect(url_for("jogo_detalhe", id_jogo=id_jogo))


# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == "__main__":
    app.run(debug=True)
