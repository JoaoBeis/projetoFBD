"""
Módulo de Carregamento e Gestão de Dados MOCK
100% Alinhado com o esquema normalizado (3FN) de:
- APFE_FINAL_132982_133155/sql/04_db_init.sql
- APFE_FINAL_132982_133155/sql/normalizacao.sql

Remove atributos derivados (golos_casa, golos_fora, orcamento, pontos_acumulados,
pontos_obtidos), move id_pavilhao de jogo para clube (1:1), desacopla jornada
de liga (calendário global) e recalcula participa_jornada.pontos_jornada.
"""

import os
import re
import json
from persistence.calculations import recalcular_pontos_jornada_plantel


def parse_sql_values(values_str):
    """
    Tokenizer e parser robusto para blocos VALUES (...) de SQL.
    Trata corretamente aspas simples escapadas ('') e tipos nulos/numéricos.
    """
    rows = []
    i = 0
    n = len(values_str)
    while i < n:
        while i < n and values_str[i] != '(':
            i += 1
        if i >= n:
            break
        i += 1  # consome '('
        row = []
        cur = []
        in_str = False
        while i < n:
            c = values_str[i]
            if in_str:
                if c == "'":
                    if i + 1 < n and values_str[i + 1] == "'":
                        cur.append("'")
                        i += 2
                        continue
                    else:
                        in_str = False
                        i += 1
                        continue
                else:
                    cur.append(c)
                    i += 1
            else:
                if c == "'":
                    in_str = True
                    i += 1
                elif c == ',':
                    val = ''.join(cur).strip()
                    row.append(val)
                    cur = []
                    i += 1
                elif c == ')':
                    val = ''.join(cur).strip()
                    row.append(val)
                    rows.append(row)
                    i += 1
                    break
                else:
                    cur.append(c)
                    i += 1
    return rows


def find_sql_path():
    """Localiza o ficheiro 04_db_init.sql em caminhos relativos prováveis."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "..", "APFE_FINAL_132982_133155", "sql", "04_db_init.sql"),
        os.path.join(base_dir, "APFE_FINAL_132982_133155", "sql", "04_db_init.sql"),
        os.path.join(os.getcwd(), "APFE_FINAL_132982_133155", "sql", "04_db_init.sql"),
        os.path.join(os.getcwd(), "..", "APFE_FINAL_132982_133155", "sql", "04_db_init.sql"),
        os.path.join(base_dir, "04_db_init.sql"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
    return None


def load_mock_data(sql_path=None):
    """
    Lê o ficheiro 04_db_init.sql e aplica as transformações de normalizacao.sql
    em memória para produzir estruturas Python alinhadas com o ER final.
    """
    if sql_path is None:
        sql_path = find_sql_path()

    json_cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_data.json")

    sql_text = None
    if sql_path and os.path.exists(sql_path):
        try:
            with open(sql_path, "r", encoding="utf-8") as f:
                sql_text = f.read()
        except Exception as e:
            print(f"[mock_data] Erro ao ler {sql_path}: {e}")

    # Fallback para cache JSON se SQL não estiver acessível
    if not sql_text:
        if os.path.exists(json_cache_path):
            try:
                with open(json_cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["MOCK_PLANTEIS"] = {int(k): v for k, v in data["MOCK_PLANTEIS"].items()}
                    data["MOCK_SELECIONA"] = {int(k): v for k, v in data["MOCK_SELECIONA"].items()}
                    return data
            except Exception as e:
                print(f"[mock_data] Erro ao carregar cache JSON: {e}")
        raise FileNotFoundError(f"Não foi possível encontrar nem o SQL ({sql_path}) nem a cache JSON.")

    def get_table_rows(table_name):
        matches = re.findall(
            rf'INSERT INTO {table_name}\s*\((.*?)\)\s*VALUES\s*(.*?);',
            sql_text,
            re.DOTALL | re.IGNORECASE,
        )
        rows = []
        for _cols, vals in matches:
            rows.extend(parse_sql_values(vals))
        return rows

    # 1. PAÍSES
    mock_paises = [
        {"nome": r[0], "sigla": r[1]}
        for r in get_table_rows("pais")
    ]

    # 2. POSIÇÕES
    mock_posicoes = [
        {"id_posicao": idx + 1, "nome": r[0], "sigla": r[1]}
        for idx, r in enumerate(get_table_rows("posicao"))
    ]
    pos_map = {p["id_posicao"]: p for p in mock_posicoes}

    # 3. PAVILHÕES
    mock_pavilhoes = [
        {"id_pavilhao": idx + 1, "nome": r[0], "capacidade": int(r[1]), "localidade": r[2]}
        for idx, r in enumerate(get_table_rows("pavilhao"))
    ]

    # 4. PESSOAS
    pessoas = {
        idx + 1: {"primeiro_nome": r[0], "apelido": r[1], "data_nasc": r[2]}
        for idx, r in enumerate(get_table_rows("pessoa"))
    }

    # 5. CLUBES E TREINADORES (normalizacao.sql: id_pavilhao movido para clube com relação 1:1)
    clubes_dict = {
        idx + 1: {
            "id_clube": idx + 1,
            "nome": r[0],
            "cidade": r[1],
            "emblema": r[2] if r[2] != "NULL" else None,
            "id_pavilhao": idx + 1,
            "treinador_nome": None,
            "treinador_licenca": None,
            "total_jogadores": 0,
        }
        for idx, r in enumerate(get_table_rows("clube"))
    }

    for r in get_table_rows("treinador"):
        tid = int(r[0])
        lic = r[1]
        cid = int(r[2])
        if cid in clubes_dict:
            p = pessoas.get(tid, {})
            clubes_dict[cid]["treinador_nome"] = f"{p.get('primeiro_nome', '')} {p.get('apelido', '')}".strip()
            clubes_dict[cid]["treinador_licenca"] = lic

    # 6. UTILIZADORES
    mock_users = [
        {"id_utilizador": idx + 1, "username": r[0], "email": r[1], "password_hash": r[2]}
        for idx, r in enumerate(get_table_rows("utilizador"))
    ]
    user_map = {u["id_utilizador"]: u for u in mock_users}

    # 7. ÁRBITROS
    mock_arbitros = []
    for r in get_table_rows("arbitro"):
        aid = int(r[0])
        p = pessoas.get(aid, {})
        mock_arbitros.append({
            "id_arbitro": aid,
            "nome": f"{p.get('primeiro_nome', '')} {p.get('apelido', '')}".strip(),
            "num_cedula": r[1],
        })

    # 8. JOGADORES
    mock_jogadores = []
    player_club_map = {}
    for r in get_table_rows("jogador"):
        jid = int(r[0])
        altura = int(r[1]) if r[1] != "NULL" else None
        peso = float(r[2]) if r[2] != "NULL" else None
        vm = float(r[3])
        pais = r[4]
        cid = int(r[5])
        pos_id = int(r[6])

        player_club_map[jid] = cid
        if cid in clubes_dict:
            clubes_dict[cid]["total_jogadores"] += 1

        p = pessoas.get(jid, {})
        pos = pos_map.get(pos_id, {})

        mock_jogadores.append({
            "id_jogador": jid,
            "primeiro_nome": p.get("primeiro_nome", ""),
            "apelido": p.get("apelido", ""),
            "data_nasc": p.get("data_nasc", ""),
            "altura": altura,
            "peso": peso,
            "valor_mercado": vm,
            "nome_pais": pais,
            "id_clube": cid,
            "clube_nome": clubes_dict.get(cid, {}).get("nome", ""),
            "id_posicao": pos_id,
            "posicao_nome": pos.get("nome", ""),
            "posicao_sigla": pos.get("sigla", ""),
        })

    mock_clubes = list(clubes_dict.values())

    # 9. PARTICIPA JOGO (sem atributo derivado pontos_obtidos)
    mock_participa_jogo = []
    for r in get_table_rows("participa_jogo"):
        jid = int(r[0])
        jogo_id = int(r[1])
        p = pessoas.get(jid, {})
        nome_jog = f"{p.get('primeiro_nome', '')} {p.get('apelido', '')}".strip()

        mock_participa_jogo.append({
            "id_jogador": jid,
            "nome": nome_jog,
            "id_jogo": jogo_id,
            "id_clube": player_club_map.get(jid),
            "golos": int(r[2]),
            "assistencias": int(r[3]),
            "remates_falhados": int(r[4]),
            "exclusoes_2min": int(r[5]),
            "cartoes_vermelhos": int(r[6]),
            "cartoes_azuis": int(r[7]),
            "defesas_gr": int(r[8]),
            "hpi": float(r[9]),
        })

    # 10. LIGAS
    mock_ligas = []
    for idx, r in enumerate(get_table_rows("liga"), 1):
        mock_ligas.append({
            "id_liga": idx,
            "nome": r[0],
            "codigo_acesso": r[1] if r[1] != "NULL" else None,
            "e_privada": r[2] == "1",
            "nome_pais": r[3] if r[3] != "NULL" else None,
            "id_utilizador": int(r[4]),
        })

    # 11. PARTICIPA LIGA (apenas id_plantel, id_liga)
    mock_participa_liga = [
        {"id_plantel": int(r[0]), "id_liga": int(r[1])}
        for r in get_table_rows("participa_liga")
    ]

    # 12. PLANTÉIS (sem atributos derivados orcamento e pontos_acumulados)
    mock_planteis = {}
    for idx, r in enumerate(get_table_rows("plantel"), 1):
        uid = int(r[3])
        u = user_map.get(uid, {})
        mock_planteis[uid] = {
            "id_plantel": idx,
            "nome_plantel": r[0],
            "id_utilizador": uid,
            "username": u.get("username", f"user_{uid}"),
        }

    # Plantel inicial para utilizador 1 (admin) para facilitar testes diretos
    if 1 not in mock_planteis and 1 in user_map:
        admin_u = user_map[1]
        admin_pid = max([p["id_plantel"] for p in mock_planteis.values()], default=0) + 1
        mock_planteis[1] = {
            "id_plantel": admin_pid,
            "nome_plantel": "Plantel Oficial HBL",
            "id_utilizador": 1,
            "username": admin_u["username"],
        }
        mock_participa_liga.append({"id_plantel": admin_pid, "id_liga": 1})

    # 13. SELECIONA
    mock_seleciona = {}
    for r in get_table_rows("seleciona"):
        pid = int(r[0])
        squad = mock_seleciona.setdefault(pid, [])
        squad.append({
            "id_jogador": int(r[1]),
            "e_titular": int(r[2]) == 1,
            "e_capitao": int(r[3]) == 1,
            "preco_compra": float(r[4]),
        })
    for p in mock_planteis.values():
        mock_seleciona.setdefault(p["id_plantel"], [])

    # 14. JORNADAS (normalizacao.sql: desligada de liga -> calendário global)
    mock_jornadas = []
    for idx, r in enumerate(get_table_rows("jornada"), 1):
        mock_jornadas.append({
            "id_jornada": idx,
            "numero_jornada": int(r[0]),
            "data_inicio": r[1],
            "data_fim": r[2],
        })

    # 15. APITA
    mock_apita = [
        {"id_arbitro": int(r[0]), "id_jogo": int(r[1])}
        for r in get_table_rows("apita")
    ]

    # 16. JOGOS (sem golos_casa, golos_fora, nem id_pavilhao)
    mock_jogos = []
    for idx, r in enumerate(get_table_rows("jogo"), 1):
        d_str = r[0][:16]  # 'YYYY-MM-DD HH:MM'
        c_casa_id = int(r[3])
        c_fora_id = int(r[4])
        jor_id = int(r[6])

        mock_jogos.append({
            "id_jogo": idx,
            "id_jornada": jor_id,
            "data_hora": d_str,
            "id_clube_casa": c_casa_id,
            "id_clube_fora": c_fora_id,
        })

    # 17. PARTICIPA JORNADA (recalculado conforme passo 3 de normalizacao.sql)
    mock_participa_jornada = []
    for r in get_table_rows("participa_jornada"):
        pid = int(r[0])
        jid = int(r[1])
        pts = recalcular_pontos_jornada_plantel(
            pid,
            jid,
            mock_seleciona.get(pid, []),
            mock_participa_jogo,
            mock_jogos,
        )
        mock_participa_jornada.append({
            "id_plantel": pid,
            "id_jornada": jid,
            "pontos_jornada": pts,
        })

    result = {
        "MOCK_PAISES": mock_paises,
        "MOCK_POSICOES": mock_posicoes,
        "MOCK_PAVILHOES": mock_pavilhoes,
        "MOCK_CLUBES": mock_clubes,
        "MOCK_USERS": mock_users,
        "MOCK_ARBITROS": mock_arbitros,
        "MOCK_JOGADORES": mock_jogadores,
        "MOCK_LIGAS": mock_ligas,
        "MOCK_PLANTEIS": mock_planteis,
        "MOCK_PARTICIPA_LIGA": mock_participa_liga,
        "MOCK_SELECIONA": mock_seleciona,
        "MOCK_JORNADAS": mock_jornadas,
        "MOCK_PARTICIPA_JORNADA": mock_participa_jornada,
        "MOCK_JOGOS": mock_jogos,
        "MOCK_APITA": mock_apita,
        "MOCK_PARTICIPA_JOGO": mock_participa_jogo,
    }

    # Salvar cache JSON atualizada para portabilidade
    try:
        with open(json_cache_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return result


# Instanciação dos dados globais na inicialização do módulo
_DATA = load_mock_data()

MOCK_PAISES = _DATA["MOCK_PAISES"]
MOCK_POSICOES = _DATA["MOCK_POSICOES"]
MOCK_PAVILHOES = _DATA["MOCK_PAVILHOES"]
MOCK_CLUBES = _DATA["MOCK_CLUBES"]
MOCK_USERS = _DATA["MOCK_USERS"]
MOCK_ARBITROS = _DATA["MOCK_ARBITROS"]
MOCK_JOGADORES = _DATA["MOCK_JOGADORES"]
MOCK_LIGAS = _DATA["MOCK_LIGAS"]
MOCK_PLANTEIS = _DATA["MOCK_PLANTEIS"]
MOCK_PARTICIPA_LIGA = _DATA["MOCK_PARTICIPA_LIGA"]
MOCK_SELECIONA = _DATA["MOCK_SELECIONA"]
MOCK_JORNADAS = _DATA["MOCK_JORNADAS"]
MOCK_PARTICIPA_JORNADA = _DATA["MOCK_PARTICIPA_JORNADA"]
MOCK_JOGOS = _DATA["MOCK_JOGOS"]
MOCK_APITA = _DATA["MOCK_APITA"]
MOCK_PARTICIPA_JOGO = _DATA["MOCK_PARTICIPA_JOGO"]
