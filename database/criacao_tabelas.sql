-- Comentário geral: A primeira parte cria o banco transacional normalizado.
-- Aqui os dados são estruturados de forma próxima ao formato original dos arquivos CSV,
-- evitando redundâncias e preparando para o processo de ETL que irá transferir
-- as informações para o Data Warehouse (esquema estrela).

CREATE DATABASE IF NOT EXISTS transacional_db;
USE transacional_db;

-- Tabela principal de CDAs (fonte: /data/001.csv)
CREATE TABLE cda (
    numCDA BIGINT PRIMARY KEY,
    anoInscricao INT NOT NULL,
    datCadastramento TIMESTAMP,
    idNaturezaDivida INT NOT NULL,
    codSituacaoCDA INT NOT NULL,
    DatSituacao TIMESTAMP,
    codFaseCobranca INT,
    ValSaldo DECIMAL(15, 2) NOT NULL
);

-- Naturezas de dívida (fonte: /data/002.csv)
CREATE TABLE naturezas_divida (
    idNaturezaDivida INT PRIMARY KEY,
    nomNaturezaDivida VARCHAR(255) NOT NULL
);

-- Situações das CDAs (fonte: /data/003.csv)
CREATE TABLE situacoes_cda (
    codSituacaoCDA INT PRIMARY KEY,
    nomSituacaoCDA VARCHAR(255) NOT NULL,
    tipoSituacao CHAR(1)
);

-- Probabilidade de recuperação (fonte: /data/004.csv)
CREATE TABLE probabilidades (
    numCDA BIGINT PRIMARY KEY,
    probRecuperacao REAL
);

-- Relação entre CDAs e Devedores (fonte: /data/005.csv)
CREATE TABLE cda_devedores (
    numCDA BIGINT NOT NULL,
    idPessoa INT NOT NULL
);

-- Devedores Pessoa Física (fonte: /data/006.csv)
CREATE TABLE devedores_pf (
    idPessoa INT PRIMARY KEY,
    descNome VARCHAR(255) NOT NULL,
    numCPF VARCHAR(14)
);

-- Devedores Pessoa Jurídica (fonte: /data/007.csv)
CREATE TABLE devedores_pj (
    idPessoa INT PRIMARY KEY,
    descNome VARCHAR(255) NOT NULL,
    numCNPJ VARCHAR(18)
);

-- Comentário geral: O código abaixo cria o banco Data Warehouse utilizando o Esquema Estrela.
-- A tabela fato (fatos_cdas) armazena os dados centrais da análise.
-- Cada dimensão representa um "atributo complexo" relacionado à tabela fato.

CREATE DATABASE IF NOT EXISTS dw_db;
USE dw_db;

-- Dimensão das naturezas das dívidas
CREATE TABLE dim_naturezas (
    id_natureza INT PRIMARY KEY,
    descricao_natureza VARCHAR(255) NOT NULL
);

-- Dimensão das situações das CDAs
CREATE TABLE dim_situacoes (
    id_situacao INT PRIMARY KEY,
    descricao_situacao VARCHAR(255) NOT NULL,
    tipo_situacao CHAR(1)
);

-- Dimensão dos devedores
CREATE TABLE dim_devedores (
    id_devedor INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    cpf_cnpj VARCHAR(18) UNIQUE,
    tipo_pessoa CHAR(2) NOT NULL
);

-- Tabela fato (informações centrais)
CREATE TABLE fatos_cdas (
    num_cda BIGINT PRIMARY KEY,
    ano_inscricao INT NOT NULL,
    data_cadastramento TIMESTAMP,
    data_situacao TIMESTAMP NOT NULL,
    valor_saldo DECIMAL(15, 2) NOT NULL,
    prob_recuperacao REAL,
    fk_natureza INT NOT NULL,
    fk_situacao INT NOT NULL,
    CONSTRAINT fk_fatos_para_naturezas FOREIGN KEY (fk_natureza) REFERENCES dim_naturezas(id_natureza),
    CONSTRAINT fk_fatos_para_situacoes FOREIGN KEY (fk_situacao) REFERENCES dim_situacoes(id_situacao)
);

-- Tabela de junção N:N entre CDAs e Devedores
CREATE TABLE jun_cdas_devedores (
    id_juncao INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    fk_cda BIGINT NOT NULL,
    fk_devedor INT NOT NULL,
    CONSTRAINT fk_juncao_para_cdas FOREIGN KEY (fk_cda) REFERENCES fatos_cdas(num_cda),
    CONSTRAINT fk_juncao_para_devedores FOREIGN KEY (fk_devedor) REFERENCES dim_devedores(id_devedor),
    CONSTRAINT uq_cda_devedor_pair UNIQUE KEY (fk_cda, fk_devedor)
);