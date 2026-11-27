"""
Funções de cálculo para atributos derivados e regras da normalização (3FN).
Alinhado com APFE_FINAL_132982_133155/sql/normalizacao.sql e apfe_final_submit.md.
"""

ORCAMENTO_INICIAL = 100_000_000.00


def calcular_pontos_jogador_jogo(stats_row):
    """
    Calcula os pontos de um jogador num jogo a partir das estatísticas base
    de participa_jogo (atributo derivado removido na 3FN).

    Fórmula oficial:
    4*golos + 2*assistencias - remates_falhados - 2*exclusoes_2min
    - 5*cartoes_vermelhos - 3*cartoes_azuis + 3*defesas_gr + 0.1*hpi
    """
    golos = int(stats_row.get("golos", 0) or 0)
    assistencias = int(stats_row.get("assistencias", 0) or 0)
    remates_falhados = int(stats_row.get("remates_falhados", 0) or 0)
    exclusoes_2min = int(stats_row.get("exclusoes_2min", 0) or 0)
    cartoes_vermelhos = int(stats_row.get("cartoes_vermelhos", 0) or 0)
    cartoes_azuis = int(stats_row.get("cartoes_azuis", 0) or 0)
    defesas_gr = int(stats_row.get("defesas_gr", 0) or 0)
    hpi = float(stats_row.get("hpi", 0.0) or 0.0)

    pontos = (
        4.0 * golos
        + 2.0 * assistencias
        - 1.0 * remates_falhados
        - 2.0 * exclusoes_2min
        - 5.0 * cartoes_vermelhos
        - 3.0 * cartoes_azuis
        + 3.0 * defesas_gr
        + 0.1 * hpi
    )
    return round(pontos, 2)


def calcular_golos_jogo(id_jogo, id_clube_casa, id_clube_fora, participa_jogo):
    """
    Calcula dinamicamente (golos_casa, golos_fora) somando os golos individuais
    registados em participa_jogo por clube.
    Devolve (None, None) se ainda não existirem estatísticas para o jogo.
    """
    rows = [s for s in participa_jogo if s["id_jogo"] == id_jogo]
    if not rows:
        return None, None

    golos_casa = sum(int(s.get("golos", 0) or 0) for s in rows if s.get("id_clube") == id_clube_casa)
    golos_fora = sum(int(s.get("golos", 0) or 0) for s in rows if s.get("id_clube") == id_clube_fora)
    return golos_casa, golos_fora


def calcular_orcamento_plantel(seleciona_rows):
    """
    Calcula (orcamento_usado, orcamento_restante) a partir da soma de
    seleciona.preco_compra face ao teto inicial de 100.000.000,00 EUR.
    """
    orcamento_usado = round(
        sum(float(s.get("preco_compra", 0.0) or 0.0) for s in seleciona_rows),
        2,
    )
    orcamento_restante = round(ORCAMENTO_INICIAL - orcamento_usado, 2)
    return orcamento_usado, orcamento_restante


def calcular_pontos_acumulados_plantel(id_plantel, participa_jornada):
    """
    Calcula os pontos acumulados de um plantel como SUM(pontos_jornada)
    em participa_jornada.
    """
    total = sum(
        float(pj.get("pontos_jornada", 0.0) or 0.0)
        for pj in participa_jornada
        if pj["id_plantel"] == id_plantel
    )
    return round(total, 2)


def recalcular_pontos_jornada_plantel(id_plantel, id_jornada, seleciona_rows, participa_jogo, jogos):
    """
    Recalcula pontos_jornada de um plantel numa jornada específica segundo
    a query de normalizacao.sql: soma dos pontos dos titulares nos jogos
    dessa jornada, com o capitão a pontuar a dobrar (2x).
    """
    starters = {s["id_jogador"]: s for s in seleciona_rows if s.get("e_titular")}
    if not starters:
        return 0.0

    jogos_jornada_ids = {jg["id_jogo"] for jg in jogos if jg["id_jornada"] == id_jornada}
    if not jogos_jornada_ids:
        return 0.0

    total = 0.0
    for pj in participa_jogo:
        if pj["id_jogo"] in jogos_jornada_ids and pj["id_jogador"] in starters:
            pts = calcular_pontos_jogador_jogo(pj)
            mult = 2.0 if starters[pj["id_jogador"]].get("e_capitao") else 1.0
            total += pts * mult
    return round(total, 2)


def obter_pavilhao_clube(id_clube, clubes, pavilhoes):
    """
    Obtém o pavilhão associado ao clube (relação 1:1 clube.id_pavilhao -> pavilhao).
    """
    clube = next((c for c in clubes if c["id_clube"] == id_clube), None)
    if not clube or not clube.get("id_pavilhao"):
        return None
    return next((p for p in pavilhoes if p["id_pavilhao"] == clube["id_pavilhao"]), None)
