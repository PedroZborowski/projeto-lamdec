# **Desafio Técnico LAMDEC - Análise de Dívida Ativa**

[](https://shields.io)

Este projeto implementa um pipeline de dados completo para o gerenciamento e análise de Certidões de Dívida Ativa (CDA). [cite\_start]A solução engloba a modelagem de um banco de dados transacional normalizado [cite: 9][cite\_start], a criação de um Data Warehouse otimizado para consultas analíticas [cite: 13][cite\_start], um processo de ETL para popular os dados [cite: 14][cite\_start], e uma API RESTful desenvolvida com FastAPI para consulta dos dados[cite: 20, 21].

## 📋 **Índice**

  * [Sobre o Projeto](https://www.google.com/search?q=%23-sobre-o-projeto)
  * [🚀 Tecnologias Utilizadas](https://www.google.com/search?q=%23-tecnologias-utilizadas)
  * [⚙️ Pré-requisitos](https://www.google.com/search?q=%23-pr%C3%A9-requisitos)
  * [▶️ Como Executar](https://www.google.com/search?q=%23-como-executar)
  * [🧪 Como Testar a API](https://www.google.com/search?q=%23-como-testar-a-api)
  * [🏛️ Arquitetura e Decisões de Design](https://www.google.com/search?q=%23%EF%B8%8F-arquitetura-e-decis%C3%B5es-de-design)
  * [📂 Estrutura do Repositório](https://www.google.com/search?q=%23-estrutura-do-reposit%C3%B3rio)
  * [👨‍💻 Autor](https://www.google.com/search?q=%23-autor)

## 📝 **Sobre o Projeto**

O desafio consiste em desenvolver uma solução de back-end robusta para tratar dados brutos de dívida ativa municipal. As principais etapas do projeto são:

  * [cite\_start]**Modelagem de um Banco Transacional:** Criação de um modelo relacional normalizado em `[Nome do seu Banco SQL, ex: PostgreSQL]` para armazenar os dados de forma íntegra e sem redundância[cite: 9, 156].
  * [cite\_start]**Data Warehouse & ETL:** Projeto e implementação de um Data Warehouse [cite: 13] [cite\_start]e de um processo de Extração, Transformação e Carga (ETL) [cite: 14] para consolidar os dados para fins analíticos.
  * [cite\_start]**API (FastAPI):** Desenvolvimento de uma API RESTful com múltiplos endpoints [cite: 21] para consultar tanto dados detalhados quanto resumos e agregações.
  * [cite\_start]**Containerização:** Orquestração de todos os serviços (bancos de dados e API) utilizando Docker e Docker Compose, garantindo um ambiente de execução consistente e facilmente replicável[cite: 19, 160].

## 🚀 **Tecnologias Utilizadas**

  * **Banco Transacional:** `PostgreSQL` | `MySQL`
  * **Data Warehouse:** `PostgreSQL` | `MySQL`
  * **ETL:** `Python (Pandas, SQLAlchemy)` | `SQL Puro`
  * **API:** `Python`, `FastAPI`
  * **Containerização:** `Docker`, `Docker Compose`

## ⚙️ **Pré-requisitos**

Para executar este projeto, você precisará ter as seguintes ferramentas instaladas em seu sistema:

  * **Docker:** [Link para instalação do Docker]
  * **Docker Compose:** [Link para instalação do Docker Compose]

## ▶️ **Como Executar**

Siga os passos abaixo para iniciar a aplicação completa:

1.  **Clone o repositório:**

    ```bash
    git clone https://coderefinery.github.io/github-without-command-line/doi/
    cd [nome-do-seu-repositorio]
    ```

2.  **Posicione os arquivos de dados:**
    Certifique-se de que os arquivos `.csv` fornecidos estejam dentro da pasta `/data`.

3.  **Inicie os containers:**
    Este comando irá construir as imagens e iniciar todos os serviços em segundo plano (`-d`).

    ```bash
    docker-compose up --build -d
    ```

4.  **Verifique o status:**
    Para confirmar que todos os containers estão rodando corretamente:

    ```bash
    docker-compose ps
    ```

    Você deverá ver os containers dos bancos de dados e da API com o status `Up` ou `running`.

## 🧪 **Como Testar a API**

Após a execução, a API estará acessível em `http://localhost:8000`. A documentação interativa (Swagger UI) gerada pelo FastAPI está disponível em:

**➡️ [http://localhost:8000/docs](https://www.google.com/search?q=http://localhost:8000/docs)**

Abaixo estão alguns exemplos de como testar os endpoints via `curl`:

#### `GET /cda/search`

*Busca CDAs com filtros dinâmicos.*

```bash
# Exemplo: Buscar CDAs de IPTU com saldo entre R$1.000 e R$5.000, ordenadas por ano
curl -X GET "http://localhost:8000/cda/search?natureza=IPTU&minSaldo=1000&maxSaldo=5000&sort_by=ano&sort_order=asc"
```

#### `GET /resumo/distribuicao_cdas`

[cite\_start]*Retorna o percentual de CDAs por situação (Em cobrança, Cancelada, Quitada) [cite: 85, 87, 90] para cada tipo de tributo.*

```bash
curl -X GET "http://localhost:8000/resumo/distribuicao_cdas"
```

## 🏛️ **Arquitetura e Decisões de Design**

Nesta seção, detalho as decisões técnicas e arquiteturais tomadas durante o desenvolvimento do projeto.

### **1. Modelagem do Banco Transacional (OLTP)**

  * **Normalização:** [Descreva aqui como você aplicou a normalização. Ex: "Adotei a 3ª Forma Normal (3FN) para estruturar o banco de dados. As entidades `CDA`, `Devedor` e `NaturezaTributo` foram separadas em tabelas distintas para eliminar redundância de dados e evitar anomalias de inserção, atualização e deleção..."]
  * **Chaves e Relacionamentos:** [Explique a lógica das chaves primárias e estrangeiras que conectam as tabelas.]

### **2. Modelagem do Data Warehouse (OLAP)**

  * **Esquema:** [Justifique sua escolha de modelagem. Ex: "Optei por um **Esquema Estrela (Star Schema)**, pois ele é ideal para as consultas analíticas e agregações exigidas pelos endpoints de resumo. A estrutura com uma tabela fato central (`fatos_cdas`) e tabelas de dimensão (`dim_devedor`, `dim_natureza`, `dim_tempo`) simplifica os `JOINs` e melhora a performance das consultas."]

### **3. Processo de ETL**

  * **Tecnologia:** [Explique a escolha da ferramenta de ETL. Ex: "O processo foi implementado em **Python com a biblioteca Pandas**, devido à sua alta capacidade de manipulação e transformação de dados em memória. Isso facilitou a limpeza (ex: tratamento de valores nulos), a transformação (ex: cálculo da idade da CDA) e o enriquecimento dos dados antes da carga no Data Warehouse."]
  * **Orquestração:** [Mencione como o ETL é executado. Ex: "O script de ETL é executado por um serviço dedicado no `docker-compose.yml`, que aguarda os bancos de dados estarem prontos para iniciar o processo, garantindo a ordem correta de inicialização."]

### **4. API (FastAPI)**

  * **Validação de Dados:** [Mencione o uso do Pydantic. Ex: "Utilizei os `Pydantic models` do FastAPI para realizar a validação automática dos tipos de dados nos parâmetros de consulta (query params), tornando a API mais robusta e segura contra entradas inválidas."]
  * **Performance:** [Se aplicável, mencione otimizações. Ex: "As consultas mais complexas, especialmente nos endpoints de resumo, foram otimizadas com a criação de índices nas colunas mais utilizadas como filtros e `JOINs` no Data Warehouse."]

## 📂 **Estrutura do Repositório**

```
.
├── api/                # Contém todo o código-fonte da API FastAPI
├── data/               # Destino dos arquivos CSV de entrada
├── database/           # Scripts SQL para criação das tabelas (transacional e DW)
├── etl/                # Código do processo de ETL
├── .gitignore          # Arquivos e pastas ignorados pelo Git
├── docker-compose.yml  # Orquestrador dos containers Docker
└── README.md           # Esta documentação
```

## 👨‍💻 **Autor**

Desenvolvido por **[Seu Nome Completo]**.

[\<img src="[https://img.shields.io/badge/linkedin-%230077B5.svg?\&style=for-the-badge\&logo=linkedin\&logoColor=white](https://www.google.com/search?q=https://img.shields.io/badge/linkedin-%25230077B5.svg%3F%26style%3Dfor-the-badge%26logo%3Dlinkedin%26logoColor%3Dwhite)" /\>][linkedin][linkedin]
[\<img src="[https://img.shields.io/badge/github-%23121011.svg?\&style=for-the-badge\&logo=github\&logoColor=white](https://www.google.com/search?q=https://img.shields.io/badge/github-%2523121011.svg%3F%26style%3Dfor-the-badge%26logo%3Dgithub%26logoColor%3Dwhite)" /\>][github][github]

-----

[linkedin]: https://www.google.com/search?q=%5Bhttps://www.linkedin.com/in/%5D\(https://www.linkedin.com/in/\)%5Bseu-usuario%5D
[github]: https://www.google.com/search?q=%5Bhttps://github.com/%5D\(https://github.com/\)%5Bseu-usuario%5D
