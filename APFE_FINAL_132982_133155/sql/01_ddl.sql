CREATE TABLE pessoa (
    id_pessoa INT IDENTITY(1,1) NOT NULL,
    primeiro_nome VARCHAR(50) NOT NULL,
    apelido VARCHAR(50) NOT NULL,
    data_nasc DATE NOT NULL,

    CONSTRAINT PESSOA_PK PRIMARY KEY (id_pessoa),
    CONSTRAINT PESSOA_DATA_NASC_CK CHECK (data_nasc <= GETDATE())
);

CREATE TABLE pais (
    nome VARCHAR(50) NOT NULL,
    sigla VARCHAR(5) NOT NULL,

    CONSTRAINT PAIS_PK PRIMARY KEY (nome)
);

CREATE TABLE posicao (
    id_posicao INT IDENTITY(1,1) NOT NULL,
    nome VARCHAR(50) NOT NULL,
    sigla VARCHAR(10) NOT NULL,

    CONSTRAINT POSICAO_PK PRIMARY KEY (id_posicao)
);

CREATE TABLE clube (
    id_clube INT IDENTITY(1,1) NOT NULL,
    nome VARCHAR(100) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    emblema VARCHAR(255) NULL,

    CONSTRAINT CLUBE_PK PRIMARY KEY (id_clube)
);

CREATE TABLE pavilhao (
    id_pavilhao INT IDENTITY(1,1) NOT NULL,
    nome VARCHAR(100) NOT NULL,
    capacidade INT NOT NULL,
    localidade VARCHAR(100) NOT NULL,

    CONSTRAINT PAVILHAO_PK PRIMARY KEY (id_pavilhao),
    CONSTRAINT PAVILHAO_CAPACIDADE_CK CHECK (capacidade > 0)
);

CREATE TABLE utilizador (
    id_utilizador INT IDENTITY(1,1) NOT NULL,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,

    CONSTRAINT UTILIZADOR_PK PRIMARY KEY (id_utilizador),
    CONSTRAINT UTILIZADOR_USERNAME_UNK UNIQUE (username),
    CONSTRAINT UTILIZADOR_EMAIL_UNK UNIQUE (email)
);

CREATE TABLE jogador (
    id_jogador INT NOT NULL,
    altura INT,
    peso DECIMAL(5,2),
    valor_mercado DECIMAL(12,2) NOT NULL DEFAULT 0,
    nome_pais VARCHAR(50) NOT NULL,
    id_clube INT NOT NULL,
    id_posicao INT NOT NULL,

    CONSTRAINT JOGADOR_PK PRIMARY KEY (id_jogador),
    CONSTRAINT JOGADOR_ALTURA_CK CHECK (altura > 0),
    CONSTRAINT JOGADOR_PESO_CK CHECK (peso > 0),
    CONSTRAINT JOGADOR_VALOR_MERCADO_CK CHECK (valor_mercado >= 0),
    CONSTRAINT JOGADOR_PESSOA_FK FOREIGN KEY (id_jogador) REFERENCES pessoa(id_pessoa) ON DELETE CASCADE,
    CONSTRAINT JOGADOR_PAIS_FK FOREIGN KEY (nome_pais) REFERENCES pais(nome),
    CONSTRAINT JOGADOR_CLUBE_FK FOREIGN KEY (id_clube) REFERENCES clube(id_clube),
    CONSTRAINT JOGADOR_POSICAO_FK FOREIGN KEY (id_posicao) REFERENCES posicao(id_posicao)
);

CREATE TABLE treinador (
    id_treinador INT NOT NULL,
    licenca VARCHAR(50) NOT NULL,
    id_clube INT NOT NULL,

    CONSTRAINT TREINADOR_PK PRIMARY KEY (id_treinador),
    CONSTRAINT TREINADOR_PESSOA_FK FOREIGN KEY (id_treinador) REFERENCES pessoa(id_pessoa) ON DELETE CASCADE,
    CONSTRAINT TREINADOR_CLUBE_FK FOREIGN KEY (id_clube) REFERENCES clube(id_clube)
);

CREATE TABLE arbitro (
    id_arbitro INT NOT NULL,
    num_cedula VARCHAR(50) NOT NULL,

    CONSTRAINT ARBITRO_PK PRIMARY KEY (id_arbitro),
    CONSTRAINT ARBITRO_NUM_CEDULA_UNK UNIQUE (num_cedula),
    CONSTRAINT ARBITRO_PESSOA_FK FOREIGN KEY (id_arbitro) REFERENCES pessoa(id_pessoa) ON DELETE CASCADE
);

CREATE TABLE liga (
    id_liga INT IDENTITY(1,1) NOT NULL,
    nome VARCHAR(100) NOT NULL,
    codigo_acesso VARCHAR(50) NULL,
    e_privada BIT NOT NULL DEFAULT 0,
    nome_pais VARCHAR(50) NULL,
    id_utilizador INT NOT NULL,

    CONSTRAINT LIGA_PK PRIMARY KEY (id_liga),
    CONSTRAINT LIGA_PAIS_FK FOREIGN KEY (nome_pais) REFERENCES pais(nome),
    CONSTRAINT LIGA_UTILIZADOR_FK FOREIGN KEY (id_utilizador) REFERENCES utilizador(id_utilizador)
);

CREATE TABLE plantel (
    id_plantel INT IDENTITY(1,1) NOT NULL,
    nome_plantel VARCHAR(100) NOT NULL,
    orcamento DECIMAL(12,2) NOT NULL DEFAULT 100000000,
    pontos_acumulados DECIMAL(10,2) NOT NULL DEFAULT 0,
    id_utilizador INT NOT NULL,

    CONSTRAINT PLANTEL_PK PRIMARY KEY (id_plantel),
    CONSTRAINT PLANTEL_UTILIZADOR_UNK UNIQUE (id_utilizador),
    CONSTRAINT PLANTEL_ORCAMENTO_CK CHECK (orcamento >= 0),
    CONSTRAINT PLANTEL_UTILIZADOR_FK FOREIGN KEY (id_utilizador) REFERENCES utilizador(id_utilizador)
);

CREATE TABLE jornada (
    id_jornada INT IDENTITY(1,1) NOT NULL,
    numero_jornada INT NOT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    id_liga INT NOT NULL,

    CONSTRAINT JORNADA_PK PRIMARY KEY (id_jornada),
    CONSTRAINT JORNADA_NUMERO_CK CHECK (numero_jornada > 0),
    CONSTRAINT JORNADA_DATAS_CK CHECK (data_fim >= data_inicio),
    CONSTRAINT JORNADA_LIGA_FK FOREIGN KEY (id_liga) REFERENCES liga(id_liga)
);

CREATE TABLE participa_liga (
    id_plantel INT NOT NULL,
    id_liga INT NOT NULL,

    CONSTRAINT PARTICIPA_LIGA_PK PRIMARY KEY (id_plantel, id_liga),
    CONSTRAINT PARTICIPA_LIGA_PLANTEL_FK FOREIGN KEY (id_plantel) REFERENCES plantel(id_plantel),
    CONSTRAINT PARTICIPA_LIGA_LIGA_FK FOREIGN KEY (id_liga) REFERENCES liga(id_liga)
);

CREATE TABLE seleciona (
    id_plantel INT NOT NULL,
    id_jogador INT NOT NULL,
    e_titular BIT NOT NULL DEFAULT 0,
    e_capitao BIT NOT NULL DEFAULT 0,
    preco_compra DECIMAL(12,2) NOT NULL,

    CONSTRAINT SELECIONA_PK PRIMARY KEY (id_plantel, id_jogador),
    CONSTRAINT SELECIONA_PRECO_COMPRA_CK CHECK (preco_compra >= 0),
    CONSTRAINT SELECIONA_PLANTEL_FK FOREIGN KEY (id_plantel) REFERENCES plantel(id_plantel),
    CONSTRAINT SELECIONA_JOGADOR_FK FOREIGN KEY (id_jogador) REFERENCES jogador(id_jogador)
);

CREATE TABLE jogo (
    id_jogo INT IDENTITY(1,1) NOT NULL,
    data_hora DATETIME NOT NULL,
    golos_casa INT NOT NULL DEFAULT 0,
    golos_fora INT NOT NULL DEFAULT 0,
    id_clube_casa INT NOT NULL,
    id_clube_fora INT NOT NULL,
    id_pavilhao INT NOT NULL,
    id_jornada INT NOT NULL,

    CONSTRAINT JOGO_PK PRIMARY KEY (id_jogo),
    CONSTRAINT JOGO_GOLOS_CASA_CK CHECK (golos_casa >= 0),
    CONSTRAINT JOGO_GOLOS_FORA_CK CHECK (golos_fora >= 0),
    CONSTRAINT JOGO_CLUBES_DIFERENTES_CK CHECK (id_clube_casa <> id_clube_fora),
    CONSTRAINT JOGO_CLUBE_CASA_FK FOREIGN KEY (id_clube_casa) REFERENCES clube(id_clube),
    CONSTRAINT JOGO_CLUBE_FORA_FK FOREIGN KEY (id_clube_fora) REFERENCES clube(id_clube),
    CONSTRAINT JOGO_PAVILHAO_FK FOREIGN KEY (id_pavilhao) REFERENCES pavilhao(id_pavilhao),
    CONSTRAINT JOGO_JORNADA_FK FOREIGN KEY (id_jornada) REFERENCES jornada(id_jornada)
);

CREATE TABLE participa_jornada (
    id_plantel INT NOT NULL,
    id_jornada INT NOT NULL,
    pontos_jornada DECIMAL(10,2) NOT NULL DEFAULT 0,

    CONSTRAINT PARTICIPA_JORNADA_PK PRIMARY KEY (id_plantel, id_jornada),
    CONSTRAINT PARTICIPA_JORNADA_PLANTEL_FK FOREIGN KEY (id_plantel) REFERENCES plantel(id_plantel),
    CONSTRAINT PARTICIPA_JORNADA_JORNADA_FK FOREIGN KEY (id_jornada) REFERENCES jornada(id_jornada)
);

CREATE TABLE apita (
    id_arbitro INT NOT NULL,
    id_jogo INT NOT NULL,

    CONSTRAINT APITA_PK PRIMARY KEY (id_arbitro, id_jogo),
    CONSTRAINT APITA_ARBITRO_FK FOREIGN KEY (id_arbitro) REFERENCES arbitro(id_arbitro),
    CONSTRAINT APITA_JOGO_FK FOREIGN KEY (id_jogo) REFERENCES jogo(id_jogo)
);

CREATE TABLE participa_no (
    id_jogador INT NOT NULL,
    id_jogo INT NOT NULL,
    golos INT NOT NULL DEFAULT 0,
    assistencias INT NOT NULL DEFAULT 0,
    remates_falhados INT NOT NULL DEFAULT 0,
    exclusoes_2min INT NOT NULL DEFAULT 0,
    cartoes_vermelhos INT NOT NULL DEFAULT 0,
    cartoes_azuis INT NOT NULL DEFAULT 0,
    defesas_gr INT NOT NULL DEFAULT 0,
    hpi DECIMAL(6,2) NOT NULL DEFAULT 0,
    pontos_obtidos DECIMAL(8,2) NOT NULL DEFAULT 0,

    CONSTRAINT PARTICIPA_NO_PK PRIMARY KEY (id_jogador, id_jogo),
    CONSTRAINT PARTICIPA_NO_GOLOS_CK CHECK (golos >= 0),
    CONSTRAINT PARTICIPA_NO_ASSISTENCIAS_CK CHECK (assistencias >= 0),
    CONSTRAINT PARTICIPA_NO_REMATES_CK CHECK (remates_falhados >= 0),
    CONSTRAINT PARTICIPA_NO_EXCLUSOES_CK CHECK (exclusoes_2min >= 0),
    CONSTRAINT PARTICIPA_NO_VERMELHOS_CK CHECK (cartoes_vermelhos >= 0),
    CONSTRAINT PARTICIPA_NO_AZUIS_CK CHECK (cartoes_azuis >= 0),
    CONSTRAINT PARTICIPA_NO_DEFESAS_CK CHECK (defesas_gr >= 0),
    CONSTRAINT PARTICIPA_NO_JOGADOR_FK FOREIGN KEY (id_jogador) REFERENCES jogador(id_jogador),
    CONSTRAINT PARTICIPA_NO_JOGO_FK FOREIGN KEY (id_jogo) REFERENCES jogo(id_jogo)
);