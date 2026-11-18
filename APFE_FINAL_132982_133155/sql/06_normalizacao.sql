USE p3g2;
GO

-- 1. MOVER id_pavilhao DE jogo PARA clube (3FN + cardinalidade 1:1 do DER)
ALTER TABLE clube ADD id_pavilhao INT NULL;
GO

UPDATE clube
SET id_pavilhao = id_clube;
GO

ALTER TABLE clube ALTER COLUMN id_pavilhao INT NOT NULL;
ALTER TABLE clube ADD CONSTRAINT CLUBE_PAVILHAO_UNK UNIQUE (id_pavilhao);
ALTER TABLE clube ADD CONSTRAINT CLUBE_PAVILHAO_FK FOREIGN KEY (id_pavilhao) REFERENCES pavilhao(id_pavilhao);
GO

ALTER TABLE jogo DROP CONSTRAINT JOGO_PAVILHAO_FK;
ALTER TABLE jogo DROP COLUMN id_pavilhao;
GO

-- 2. DESLIGAR jornada DE liga E GARANTIR UNICIDADE DE numero_jornada
ALTER TABLE jornada DROP CONSTRAINT JORNADA_LIGA_FK;
ALTER TABLE jornada DROP COLUMN id_liga;
ALTER TABLE jornada ADD CONSTRAINT JORNADA_NUMERO_UNK UNIQUE (numero_jornada);
GO

-- 3. RECALCULAR participa_jornada.pontos_jornada COM BASE NOS TITULARES/CAPITÃO
UPDATE participa_jornada
SET pontos_jornada = 0;

UPDATE participa_jornada
SET pontos_jornada = (
    SELECT ROUND(SUM(
        (
            4.0 * pj.golos
            + 2.0 * pj.assistencias
            - 1.0 * pj.remates_falhados
            - 2.0 * pj.exclusoes_2min
            - 5.0 * pj.cartoes_vermelhos
            - 3.0 * pj.cartoes_azuis
            + 3.0 * pj.defesas_gr
            + 0.1 * pj.hpi
        ) * CASE WHEN s.e_capitao = 1 THEN 2.0 ELSE 1.0 END
    ), 2)
    FROM seleciona AS s
    INNER JOIN participa_jogo AS pj ON pj.id_jogador = s.id_jogador
    INNER JOIN jogo AS jg ON jg.id_jogo = pj.id_jogo
    WHERE s.e_titular = 1
      AND s.id_plantel = participa_jornada.id_plantel
      AND jg.id_jornada = participa_jornada.id_jornada
)
WHERE EXISTS (
    SELECT *
    FROM seleciona AS s
    INNER JOIN participa_jogo AS pj ON pj.id_jogador = s.id_jogador
    INNER JOIN jogo AS jg ON jg.id_jogo = pj.id_jogo
    WHERE s.e_titular = 1
      AND s.id_plantel = participa_jornada.id_plantel
      AND jg.id_jornada = participa_jornada.id_jornada
);
GO

-- 4. REMOVER ATRIBUTOS DERIVADOS/REDUNDANTES (plantel, jogo, participa_jogo)
-- Remover DEFAULT constraints associadas às colunas que vão ser apagadas
DECLARE @tabela VARCHAR(100), @constraint VARCHAR(200), @cmd VARCHAR(500);

WHILE EXISTS (
    SELECT *
    FROM sys.default_constraints
    WHERE (OBJECT_NAME(parent_object_id) = 'plantel' AND COL_NAME(parent_object_id, parent_column_id) IN ('orcamento', 'pontos_acumulados'))
       OR (OBJECT_NAME(parent_object_id) = 'jogo' AND COL_NAME(parent_object_id, parent_column_id) IN ('golos_casa', 'golos_fora'))
       OR (OBJECT_NAME(parent_object_id) = 'participa_jogo' AND COL_NAME(parent_object_id, parent_column_id) = 'pontos_obtidos')
)
BEGIN
    SELECT
        @tabela = OBJECT_NAME(parent_object_id),
        @constraint = name
    FROM sys.default_constraints
    WHERE (OBJECT_NAME(parent_object_id) = 'plantel' AND COL_NAME(parent_object_id, parent_column_id) IN ('orcamento', 'pontos_acumulados'))
       OR (OBJECT_NAME(parent_object_id) = 'jogo' AND COL_NAME(parent_object_id, parent_column_id) IN ('golos_casa', 'golos_fora'))
       OR (OBJECT_NAME(parent_object_id) = 'participa_jogo' AND COL_NAME(parent_object_id, parent_column_id) = 'pontos_obtidos');

    SET @cmd = 'ALTER TABLE ' + @tabela + ' DROP CONSTRAINT ' + @constraint + ';';
    EXEC (@cmd);
END;
GO

ALTER TABLE plantel DROP CONSTRAINT PLANTEL_ORCAMENTO_CK;
ALTER TABLE plantel DROP COLUMN orcamento, pontos_acumulados;
GO

ALTER TABLE jogo DROP CONSTRAINT JOGO_GOLOS_CASA_CK;
ALTER TABLE jogo DROP CONSTRAINT JOGO_GOLOS_FORA_CK;
ALTER TABLE jogo DROP COLUMN golos_casa, golos_fora;
GO

ALTER TABLE participa_jogo DROP COLUMN pontos_obtidos;
GO

-- 5. ADICIONAR RESTRIÇÕES DE CHAVES CANDIDATAS (BCNF) E INTEGRIDADE DE DOMÍNIO
ALTER TABLE pais ADD CONSTRAINT PAIS_SIGLA_UNK UNIQUE (sigla);
ALTER TABLE posicao ADD CONSTRAINT POSICAO_NOME_UNK UNIQUE (nome);
ALTER TABLE posicao ADD CONSTRAINT POSICAO_SIGLA_UNK UNIQUE (sigla);
ALTER TABLE treinador ADD CONSTRAINT TREINADOR_CLUBE_UNK UNIQUE (id_clube);

ALTER TABLE liga ADD CONSTRAINT LIGA_PRIVADA_CODIGO_CK
    CHECK ((e_privada = 0 AND codigo_acesso IS NULL) OR (e_privada = 1 AND codigo_acesso IS NOT NULL));
CREATE UNIQUE INDEX UX_LIGA_CODIGO_ACESSO ON liga(codigo_acesso) WHERE codigo_acesso IS NOT NULL;

ALTER TABLE seleciona ADD CONSTRAINT SELECIONA_CAPITAO_TITULAR_CK
    CHECK (e_capitao = 0 OR e_titular = 1);
CREATE UNIQUE INDEX UX_SELECIONA_UM_CAPITAO ON seleciona(id_plantel) WHERE e_capitao = 1;

ALTER TABLE participa_jogo ADD CONSTRAINT PARTICIPA_JOGO_CARTOES_CK
    CHECK (cartoes_vermelhos <= 1 AND cartoes_azuis <= 1);
GO