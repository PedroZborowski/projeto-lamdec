--Comentário geral: Eu utilizei o esquema chamado de Esquema Estrela, onde a informação central é a tabela
--fato (que possui o dado central analizado, nesse caso os CDAs), e a mesma possui uma chave estrangeira para
--cada tabela de dimensões (como se fosse um atributo "complexo").

CREATE DATABASE IF NOT EXISTS desafio_db;
USE desafio_db;

--Dimensão das naturezas das dívidas (fonte: /data/002.csv)
CREATE TABLE dim_naturezas (
    id_natureza INT PRIMARY KEY,
    descricao_natureza VARCHAR(255) NOT NULL
);

--Dimensão das situações dos CDAs (fonte: /data/003.csv)
CREATE TABLE dim_situacoes (
    id_situacao INT PRIMARY KEY,
    descricao_situacao VARCHAR(255) NOT NULL,
    tipo_situacao CHAR(1)
);

--Dimensão dos devedores (fontes: /data/006.csv e /data/007.csv)
CREATE TABLE dim_devedores (
    id_devedor INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    cpf_cnpj VARCHAR(18) UNIQUE,
    tipo_pessoa CHAR(2) NOT NULL
);

--Tabela fato (as informações centrais. Fontes: /data/001.csv e /data/004.csv)
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

--Tabela de junção: Ligação N:N entre CDAs e os devedores associados (fonte: /data/005.csv)
--OBS: No final a UNIQUE KEY é criada para que o par em si seja um valor único.
CREATE TABLE jun_cdas_devedores (
    id_juncao INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    fk_cda BIGINT NOT NULL,
    fk_devedor INT NOT NULL,

    CONSTRAINT fk_juncao_para_cdas 
        FOREIGN KEY (fk_cda) REFERENCES fatos_cdas(num_cda),
        
    CONSTRAINT fk_juncao_para_devedores 
        FOREIGN KEY (fk_devedor) REFERENCES dim_devedores(id_devedor),

    CONSTRAINT uq_cda_devedor_pair 
        UNIQUE KEY (fk_cda, fk_devedor)
);