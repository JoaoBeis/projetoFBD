-- normalizacao.sql

-- Aplica a normalizacao (3FN) a BD criada por 01_ddl.sql + 04_db_init.sql.
-- Corresponde ao DER/ER finais.

-- ORDEM DE EXECUCAO: 01_ddl.sql -> 04_db_init.sql -> normalizacao.sql
-- Correr UMA vez, sobre uma BD acabada de criar com 01 e 04.

USE p3g2;
GO

-- Necessario para criar os indices filtrados do passo 5
SET QUOTED_IDENTIFIER ON;
SET ANSI_NULLS ON;
GO

-- 1. MOVER id_pavilhao DE jogo PARA clube (3FN: id_clube_casa -> id_pavilhao)
ALTER TABLE dbo.clube ADD id_pavilhao INT NULL;
GO

-- cada clube joga no pavilhao com o mesmo id (mesma cidade; confirmado no passo seguinte)
UPDATE dbo.clube
SET id_pavilhao = id_clube;
GO

-- verificacao (esperado: 0): nenhum jogo em casa num pavilhao diferente do do clube
SELECT COUNT(*) AS jogos_com_pavilhao_diferente
FROM dbo.jogo AS j
INNER JOIN dbo.clube AS c ON c.id_clube = j.id_clube_casa
WHERE c.id_pavilhao <> j.id_pavilhao;
GO

ALTER TABLE dbo.clube ALTER COLUMN id_pavilhao INT NOT NULL;
ALTER TABLE dbo.clube ADD CONSTRAINT CLUBE_PAVILHAO_UNK UNIQUE (id_pavilhao);
ALTER TABLE dbo.clube ADD CONSTRAINT CLUBE_PAVILHAO_FK
    FOREIGN KEY (id_pavilhao) REFERENCES dbo.pavilhao(id_pavilhao);
GO

ALTER TABLE dbo.jogo DROP CONSTRAINT JOGO_PAVILHAO_FK;
ALTER TABLE dbo.jogo DROP COLUMN id_pavilhao;
GO

-- 2. DESLIGAR jornada DE liga (jornada = calendario real, global)
ALTER TABLE dbo.jornada DROP CONSTRAINT JORNADA_LIGA_FK;
ALTER TABLE dbo.jornada DROP COLUMN id_liga;
ALTER TABLE dbo.jornada ADD CONSTRAINT JORNADA_NUMERO_UNK UNIQUE (numero_jornada);
GO

-- 3. RECALCULAR participa_jornada.pontos_jornada
--    pontos = soma dos pontos dos titulares nos jogos da jornada, capitao a dobrar
--    pontos de um jogador = 4*golos + 2*assistencias - remates_falhados - 2*exclusoes_2min
--                           - 5*cartoes_vermelhos - 3*cartoes_azuis + 3*defesas_gr + 0.1*hpi
UPDATE pjor
SET pjor.pontos_jornada = ISNULL(x.pontos, 0.00)
FROM dbo.participa_jornada AS pjor
LEFT JOIN (
    SELECT s.id_plantel, jg.id_jornada,
           CAST(SUM(
               ROUND(
                   4.0 * pj.golos
                   + 2.0 * pj.assistencias
                   - 1.0 * pj.remates_falhados
                   - 2.0 * pj.exclusoes_2min
                   - 5.0 * pj.cartoes_vermelhos
                   - 3.0 * pj.cartoes_azuis
                   + 3.0 * pj.defesas_gr
                   + 0.1 * pj.hpi, 2
               ) * CASE WHEN s.e_capitao = 1 THEN 2.0 ELSE 1.0 END
           ) AS DECIMAL(10,2)) AS pontos
    FROM dbo.seleciona AS s
    INNER JOIN dbo.participa_jogo AS pj ON pj.id_jogador = s.id_jogador
    INNER JOIN dbo.jogo AS jg ON jg.id_jogo = pj.id_jogo
    WHERE s.e_titular = 1
    GROUP BY s.id_plantel, jg.id_jornada
) AS x ON x.id_plantel = pjor.id_plantel AND x.id_jornada = pjor.id_jornada;
GO

-- 4. REMOVER ATRIBUTOS DERIVADOS
--    plantel.orcamento, plantel.pontos_acumulados, jogo.golos_casa, jogo.golos_fora,
--    participa_jogo.pontos_obtidos
--    Primeiro apagam-se as constraints DEFAULT (nomes gerados automaticamente pelo 01_ddl.sql)
DECLARE @tabela VARCHAR(100), @constraint VARCHAR(200), @cmd VARCHAR(500);

WHILE EXISTS (
    SELECT 1
    FROM sys.default_constraints
    WHERE (OBJECT_NAME(parent_object_id) = 'plantel' AND COL_NAME(parent_object_id, parent_column_id) IN ('orcamento', 'pontos_acumulados'))
       OR (OBJECT_NAME(parent_object_id) = 'jogo' AND COL_NAME(parent_object_id, parent_column_id) IN ('golos_casa', 'golos_fora'))
       OR (OBJECT_NAME(parent_object_id) = 'participa_jogo' AND COL_NAME(parent_object_id, parent_column_id) = 'pontos_obtidos')
)
BEGIN
    SELECT TOP 1
        @tabela = OBJECT_NAME(parent_object_id),
        @constraint = name
    FROM sys.default_constraints
    WHERE (OBJECT_NAME(parent_object_id) = 'plantel' AND COL_NAME(parent_object_id, parent_column_id) IN ('orcamento', 'pontos_acumulados'))
       OR (OBJECT_NAME(parent_object_id) = 'jogo' AND COL_NAME(parent_object_id, parent_column_id) IN ('golos_casa', 'golos_fora'))
       OR (OBJECT_NAME(parent_object_id) = 'participa_jogo' AND COL_NAME(parent_object_id, parent_column_id) = 'pontos_obtidos');

    SET @cmd = 'ALTER TABLE dbo.' + @tabela + ' DROP CONSTRAINT ' + @constraint + ';';
    EXEC (@cmd);
END;
GO

ALTER TABLE dbo.plantel DROP CONSTRAINT PLANTEL_ORCAMENTO_CK;
ALTER TABLE dbo.plantel DROP COLUMN orcamento, pontos_acumulados;
GO

ALTER TABLE dbo.jogo DROP CONSTRAINT JOGO_GOLOS_CASA_CK;
ALTER TABLE dbo.jogo DROP CONSTRAINT JOGO_GOLOS_FORA_CK;
ALTER TABLE dbo.jogo DROP COLUMN golos_casa, golos_fora;
GO

ALTER TABLE dbo.participa_jogo DROP COLUMN pontos_obtidos;
GO

-- 5. CHAVES CANDIDATAS (UNIQUE) E INTEGRIDADE DE DOMINIO
ALTER TABLE dbo.pais      ADD CONSTRAINT PAIS_SIGLA_UNK      UNIQUE (sigla);
ALTER TABLE dbo.posicao   ADD CONSTRAINT POSICAO_NOME_UNK    UNIQUE (nome);
ALTER TABLE dbo.posicao   ADD CONSTRAINT POSICAO_SIGLA_UNK   UNIQUE (sigla);
ALTER TABLE dbo.clube     ADD CONSTRAINT CLUBE_NOME_UNK      UNIQUE (nome);
ALTER TABLE dbo.pavilhao  ADD CONSTRAINT PAVILHAO_NOME_UNK   UNIQUE (nome);
ALTER TABLE dbo.treinador ADD CONSTRAINT TREINADOR_CLUBE_UNK UNIQUE (id_clube);
GO

-- liga privada <=> tem codigo de acesso (o indice filtrado garante codigo unico; UNIQUE normal so admite 1 NULL)
ALTER TABLE dbo.liga ADD CONSTRAINT LIGA_PRIVADA_CODIGO_CK
    CHECK ((e_privada = 0 AND codigo_acesso IS NULL) OR (e_privada = 1 AND codigo_acesso IS NOT NULL));
CREATE UNIQUE INDEX UX_LIGA_CODIGO_ACESSO ON dbo.liga(codigo_acesso) WHERE codigo_acesso IS NOT NULL;
GO

-- o capitao tem de ser titular; no maximo 1 capitao por plantel
ALTER TABLE dbo.seleciona ADD CONSTRAINT SELECIONA_CAPITAO_TITULAR_CK
    CHECK (e_capitao = 0 OR e_titular = 1);
CREATE UNIQUE INDEX UX_SELECIONA_UM_CAPITAO ON dbo.seleciona(id_plantel) WHERE e_capitao = 1;
GO

-- no maximo 1 cartao vermelho e 1 azul por jogador e jogo
ALTER TABLE dbo.participa_jogo ADD CONSTRAINT PARTICIPA_JOGO_CARTOES_CK
    CHECK (cartoes_vermelhos <= 1 AND cartoes_azuis <= 1);
GO