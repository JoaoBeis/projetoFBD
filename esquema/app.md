# Walkthrough — Aplicação Alinhada com a Normalização (3FN)

Todas as alterações estruturais definidas em normalizacao.sql, 04_db_init.sql, apfe_final_submit.md, der.jpg e er.jpg foram aplicadas à pasta `app/`, mantendo a aplicação a funcionar integralmente com dados mock.

---

## Alterações Realizadas

### 1. Cálculos Derivados e Regras da 3FN
- **[calculations.py]** *(Novo)*:
  - `ORCAMENTO_INICIAL = 100_000_000.00`
  - `calcular_pontos_jogador_jogo`: calcula os pontos fantasy pela fórmula `4*golos + 2*assistencias - remates_falhados - 2*exclusoes_2min - 5*cartoes_vermelhos - 3*cartoes_azuis + 3*defesas_gr + 0.1*hpi`.
  - `calcular_golos_jogo`: soma os golos individuais de `MOCK_PARTICIPA_JOGO` por clube (devolve `(None, None)` quando não existem registos de jogo, mantendo `VS` para encontros agendados).
  - `calcular_orcamento_plantel`: devolve `(orcamento_usado, orcamento_restante)` a partir da soma de `seleciona.preco_compra`.
  - `calcular_pontos_acumulados_plantel`: soma `participa_jornada.pontos_jornada`.
  - `recalcular_pontos_jornada_plantel`: recalcula os pontos da jornada considerando apenas titulares (`e_titular = True`) e duplicando o capitão (`e_capitao = True`).
  - `obter_pavilhao_clube`: resolve a relação 1:1 `clube.id_pavilhao -> pavilhao`.

### 2. Estruturas Mock
- **[mock_data.py]** e **[mock_data.json]**:
  - Removidos os atributos derivados armazenados: `golos_casa` e `golos_fora` (de `MOCK_JOGOS`), `orcamento` e `pontos_acumulados` (de `MOCK_PLANTEIS`), e `pontos_obtidos` (de `MOCK_PARTICIPA_JOGO`).
  - Movido `id_pavilhao` de `MOCK_JOGOS` para `MOCK_CLUBES` (`id_pavilhao = id_clube`, relação 1:1).
  - Desacoplada `MOCK_JORNADAS` de `liga` (removidos `id_liga` e `nome_liga`; `id_jornada` PK e `numero_jornada` global).
  - Mantido `MOCK_PARTICIPA_LIGA` com `(id_plantel, id_liga)` e `MOCK_PARTICIPA_JORNADA` com `(id_plantel, id_jornada, pontos_jornada)` recalculado conforme a query do `normalizacao.sql`.
  - Removida a estrutura estática `HISTORICO_JOGOS` do JSON (passa a ser construída dinamicamente em `app.py`).

### 3. Rotas e Validações Flask
- **[app.py]**:
  - Adicionados helpers de enriquecimento (`enrich_plantel`, `enrich_jogo`, `enrich_clube`, `enrich_jogador`, `build_historico_jogos`, `recalculate_jornada_standings`) para calcular valores em tempo real sem persistir campos derivados nos dicionários mock.
  - `/meu-plantel/toggle-titular` e `/meu-plantel/toggle-capitao`: aplicam a restrição `SELECIONA_CAPITAO_TITULAR_CK` (capitão tem de ser titular) e `UX_SELECIONA_UM_CAPITAO` (no máximo 1 capitão).
  - `/ligas/criar`: aplica `LIGA_PRIVADA_CODIGO_CK` e `UX_LIGA_CODIGO_ACESSO` (liga privada requer código de acesso único; liga pública força `codigo_acesso = None`).
  - `/jogos/criar`: remove leitura de `id_pavilhao`; o pavilhão passa a ser inferido pelo clube visitado.
  - `/jogos/<id_jogo>/estatisticas`: remove `pontos_obtidos` do formulário, valida `PARTICIPA_JOGO_CARTOES_CK` (`cartoes_vermelhos <= 1`, `cartoes_azuis <= 1`) e recalcula `MOCK_PARTICIPA_JORNADA` para a jornada do encontro.

### 4. Templates HTML
- **[jogos.html]**: removido `<select name="id_pavilhao">` do modal de agendamento e referências a liga nas jornadas; exibido o pavilhão inferido do clube da casa.
- **[jogo_detalhe.html]**: removido o input `pontos_obtidos` do formulário, mantendo o cálculo dinâmico na coluna `Pts` e no placar; pavilhão obtido pelo clube da casa.
- **[plantel.html]**: apresenta `Utilizado` (`orcamento_usado`), `Disponível` (`orcamento_restante`) e `Pts Acumulados` (`pontos_acumulados`), bloqueando a promoção a capitão de jogadores suplentes na interface.
- **[clubes.html]**: exibe o pavilhão associado 1:1 a cada clube (`pavilhao_nome`, `pavilhao_capacidade`).
- **[ligas.html]**: validação dinâmica de `codigo_acesso` obrigatório quando selecionada liga privada.

---

## Verificação e Testes


1. **Validação estrutural e funcional via `app.test_client()`**:
- Verificado que `MOCK_JOGOS`, `MOCK_PLANTEIS`, `MOCK_PARTICIPA_JOGO` e `MOCK_JORNADAS` (em memória e em `mock_data.json`) não contêm atributos derivados nem `id_liga` em `jornada`.
  - Verificadas as fórmulas de cálculo de pontos, soma de golos por clube, orçamento utilizado/disponível e pontos acumulados.
  - Testados todos os fluxos `GET` e `POST` (`/login`, `/meu-plantel`, `/meu-plantel/toggle-titular`, `/meu-plantel/toggle-capitao`, `/jogos/criar`, `/jogos/<id>/estatisticas`, `/ligas/criar`) — resultado: `ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!`.

2. **Validação no servidor Flask ativo (`http://127.0.0.1:5000`)**:
- Todas as rotas principais (`/`, `/login`, `/plantel/1`, `/ligas`, `/ligas/1`, `/jogadores`, `/clubes`, `/jogos`, `/jogos/1`) responderam com código HTTP `200`.