# BD: Trabalho Prático APF-T

**Grupo**: P3G2
- João Reis, MEC: 132982
- Rúben Marques, MEC: 133155

## Introdução / Introduction
 
Este projeto consiste no desenvolvimento da base de dados para uma plataforma de Fantasy Handball. A ideia principal é permitir que qualquer utilizador crie ou entre em ligas virtuais e monte o seu próprio plantel com jogadores reais de andebol. Planeamos que a pontuação de cada plantel seja calculada dependendo do desempenho verdadeiro dos atletas em cada jogo e jornada da vida real (Se necessário iremos adicionar dados fictícios para manter coerência com o diagrama e esquema, ou se acharmos necessário ao longo do projeto).

## ​Análise de Requisitos / Requirements

Ao criar as entidades existentes numa Fantasy percebemos que iriam haver entidades que representariam coisas reais e outras que representariam coisas virtuais, criadas por um utilizador ou calculadas através dos dados reais.

Para as entidades reais, começámos a definir as pessoas, e como todas as pessoas iam ter coisas em comum, decidimos usar uma herança IS-A para jogadores, treinadores e árbitros, que por sua vez vão ter os seus atributos e relações próprias.
Passando para os jogos, que é uma das entidades mais importantes pois é a que envolve mais interações, escolhemos associar as estatísticas dos jogadores aos jogos, pois temos dados por jogador mas mais à frente para cada jornada iremos precisar destas mesma estatística por jogo para cada jogador. Assim esta relação irá ter os atributos que registam o que cada jogador faz em cada partida. 
Tivemos ainda atenção à relação entre clubes e jogos, pois num jogo é obrigatório 2 equipas, 1 visitante e 1 visitada.
Ainda temos algumas entidades para paises, posições e pavilhões, que apesar de serem mais secundárias, foram feitas com a ideia de complementar algumas ações possíveis que um utilizador poderá querer fazer relativamente à sua liga ou plantel.

Para as entidades virtuais, pensamos da perspetiva do utilizador, pois ele vai controlar tudo. Cada utilizador registado pode ter o seu próprio plantel, e em cada plantel precisamos saber o preço de compra a partir do preço atual do jogador, quem é titular e não titular (suplente), e quem é capitao. Isto irá servir para calcular os pontos nas jornadas.
O mesmo plantel pode competir em várias ligas ao mesmo tempo, quer sejam públicas ou privadas criadas entre amigos. Além disso, em vez de guardarmos o total acumulado de pontos (que é um atributo derivado), decidimos guardar apenas os pontos por jornada. Desta forma, o utilizador consegue acompanhar o seu histórico e calculamos dinamicamente os pontos acumulados na liga.
Uma liga pode também ser relativa a uma país, mas já é opcional.

## DER - Diagrama Entidade Relacionamento/Entity Relationship Diagram

### Versão final/Final version

![DER Diagram!](der.jpg "AnImage")

## ER - Esquema Relacional/Relational Schema

### Versão final/Final Version

![ER Diagram!](er.jpg "AnImage")

## ​SQL DDL - Data Definition Language

[SQL DDL File](sql/01_ddl.sql "SQLFileQuestion")

## Normalização / Normalization

Após a definição do esquema inicial (`DDL` e `DML`), procedeu-se à análise e normalização da base de dados (implementada no script `06_normalizacao.sql`) com o objetivo de atingir a Terceira Forma Normal (3FN), eliminar redundâncias e reforçar a integridade dos dados.

### 1. Remoção de Atributos Derivados e Redundantes
Para evitar anomalias de atualização e inconsistências entre valores armazenados e valores calculados, foram eliminados os atributos derivados que podem ser obtidos dinamicamente através de consultas (`SELECT` / *Views*):

* **`Plantel.orcamento`:** Removido por ser calculável a partir do orçamento inicial definido para a plataforma subtraído da soma dos `preco_compra` dos jogadores associados ao plantel (`Seleciona`).
* **`Plantel.pontos_acumulados`:** Removido por corresponder ao somatório dos `pontos_jornada` registados para cada plantel na tabela `Participa_Jornada`.
* **`Jogo.golos_casa` e `Jogo.golos_fora`:** Removidos por poderem ser apurados diretamente através da soma dos golos marcados pelos jogadores de cada clube no respetivo jogo (`Participa_Jogo`).
* **`Participa_Jogo.pontos_obtidos`:** Removido por representar uma pontuação derivada da aplicação das regras de pontuação da *Fantasy* às estatísticas individuais registadas no jogo (golos, assistências, defesas, sanções, etc.).

### 2. Reestruturação de Dependências Funcionais
* **Transferência de `id_pavilhao` (`Jogo` $\rightarrow$ `Clube`):** No modelo inicial, o pavilhão estava associado diretamente a `Jogo`. Contudo, no contexto da competição, o pavilhão onde se realiza o encontro é determinado pelo clube visitado (`id_clube_casa`), gerando uma dependência transitiva ($Jogo \rightarrow Clube_{casa} \rightarrow Pavilhao$). Ao mover `id_pavilhao` para `Clube` (numa relação 1:1), elimina-se esta dependência transitiva e garante-se a 3FN.
* **Desacoplamento entre `Jornada` e `Liga`:** Uma vez que as jornadas correspondem ao calendário real dos jogos de andebol e que um mesmo plantel pode competir simultaneamente em várias ligas virtuais (públicas ou privadas), removeu-se a chave estrangeira `id_liga` de `Jornada`. A ligação entre jornadas, plantéis e ligas passa a ser assegurada de forma consistente através de `Participa_Jornada` e `Participa_Liga`.

### 3. Restrições de Integridade e Atualização de Dados
* **Chaves Candidatas (`UNIQUE`):** Adicionadas restrições de unicidade sobre atributos naturais (`pais.sigla`, `posicao.nome`, `posicao.sigla`, `treinador.id_clube`, `clube.id_pavilhao` e `jornada.numero_jornada`) para impedir registos duplicados.
* **Integridade de Domínio (`CHECK`):** Introduzidas validações ao nível do esquema para garantir a coerência dos dados (valores não negativos para preços, capacidades e estatísticas de jogo, distinção obrigatória entre clube visitado e visitante num jogo, e validação das regras de titularidade/capitão).
* **Recálculo de Pontuações:** Atualização dos valores de `Participa_Jornada.pontos_jornada` para refletir de forma exata o desempenho estatístico dos atletas titulares e do capitão em cada jornada.