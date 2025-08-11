# **Desafio Técnico LAMDEC - Análise de Dívida Ativa**

Este projeto implementa um pipeline de dados completo para o gerenciamento e análise de Certidões de Dívida Ativa (CDA). A solução engloba a modelagem de um banco de dados transacional normalizado, a criação de um Data Warehouse otimizado para consultas analíticas, um processo de ETL para popular os dados e uma APIdesenvolvida com FastAPI para consulta dos dados.

## **Índice**

  * **Sobre o Projeto**
  * **Tecnologias Utilizadas**
  * **Pré-requisitos**
  * **Como Executar**
  * **Como Testar a API**
  * **Arquitetura e Decisões de Design**
  * **Autor**

##  **Sobre o Projeto**

O desafio consiste em desenvolver uma solução de back-end robusta para tratar dados brutos de dívida ativa municipal. As principais etapas do projeto são:

  * **Modelagem de um Banco Transacional:** Criação de um modelo relacional normalizado em `MySQL` para armazenar os dados de forma íntegra e sem redundância.
  * **Data Warehouse & ETL:** Projeto e implementação de um Data Warehouse e de um processo de Extração, Transformação e Carga (ETL) para consolidar os dados para fins analíticos.
  * **API (FastAPI):** Desenvolvimento de uma API com múltiplos endpoints para consultar tanto dados detalhados quanto resumos e agregações.
  * **Containerização:** Orquestração de todos os serviços (bancos de dados e API) utilizando Docker e Docker Compose, garantindo um ambiente de execução consistente e facilmente replicável.
  * **EXTRA: Escalabilidade:** Uso de nginx para permitir a abertura de múltiplas instâncias de servidores, permitindo escalabilidade no caso de sobrecarga.

##  **Tecnologias Utilizadas**

  * **Banco Transacional:** `MySQL`
  * **Data Warehouse:** `MySQL`
  * **ETL:** `Python (Pandas, SQLAlchemy)` | `SQL Puro`
  * **API:** `Python`, `FastAPI`
  * **Containerização:** `Docker`, `Docker Compose`
  * **Escalabilidade:** `Nginx`, `Docker Compose`

##  **Pré-requisitos**

Para executar este projeto, você precisará ter a seguinte ferramenta instalada em seu sistema:

  * **Docker:** https://www.docker.com (nas versões mais recentes, já vem com docker compose)

##  **Como Executar**

Siga os passos abaixo para iniciar a aplicação completa:

1.  **Clone o repositório e entre no seu diretório:**

    ```bash
    git clone https://github.com/PedroZborowski/projeto-lamdec
    cd projeto-lamdec
    ```

2.  **Renomeie e edite o arquivo .env.example:**
    As instruções para essa etapa estão dentro do próprio arquivo.

3.  **IMPORTANTE: Cuidado com a porta 3306**
    A variável DB_HOST_PORT possui instruções especiais, também no arquivo. Ignorar essa etapa causará erros no banco de dados.

4.  **Inicie os containers:**
    Este comando irá construir as imagens e iniciar todos os serviços em segundo plano (`-d`).

    ```bash
    docker compose up --build -d
    ```
    Aviso: esse processo pode demorar um tempo. Aguarde até que esteja pronto para prosseguir para a próxima instrução.

5.  **Verifique o status:**
    Esse comando mostra o comportamento dos containers.

    ```bash
    docker compose ps
    ```

6.  **EXTRA Rodar mais instâncias:**
    Você pode alterar a quantidade de instâncias de servidor usando a flag (`--scale`)

    ```bash
    docker compose up --scale api=4 -d
    ```

7.  **Parar os containers**
    Se você quiser parar a execução, você pode usar o seguinte comando:

    ```bash
    docker compose down
    ```

8.  **Reiniciar os containers**
    Para reiniciar é simples: basta usar o comando inicial sem a flag (`--build`)

    ```bash
    docker compose up
    ```

##  **Como Testar a API**

Enquanto os containers estiverem ativos, a API estará acessível em `http://localhost`. A documentação interativa (Swagger UI) gerada pelo FastAPI está disponível em:

http://localhost/docs

Nesse link, você conseguirá testar os endpoints e requisições a partir de uma interface extremamente intuitiva.

##  **Arquitetura e Decisões de Design**

Nesta seção, detalho as decisões técnicas e arquiteturais tomadas durante o desenvolvimento do projeto.

### **1. Modelagem do Banco Transacional**

  Para o banco transacional, tentei normalizar o máximo de informações possível. A maioria dos tratamentos foi relacionado a linhas duplicadas e remoção de colunas inúteis. Esse processo está extremamente detalhado na script "pipeline.py".

### **2. Modelagem do Data Warehouse**

  Para o Data Warehouse, me baseei no esquema chamado esquema estrela. Ele centraliza a principal fonte de análise (os cdas) na tabela fato, e agrupa o resto em "atributos complexos", separando-os em outra tabela chamada tabela de dimensão. A conexão entre a tabela fato e as dimensões é feita por meio de chaves estrangeiras. Também precisei criar uma tabela de junção para futuramente facilitar algumas buscas. Essa tabela une o CDA ao seu respectivo devedor.

### **3. Processo de ETL**

  O ETL é feito utilizando principalmente a biblioteca pandas. Extract simplesmente extrai os arquivos com a função "read_csv". Transform é a etapa mais difícil. Como descrito na modelagem do banco transacional, a transformação é a etapa mais demorada e complexa, e compõe a maior parte do código "pipeline.py". Os métodos de transformação estão todos lá descritos. Por fim, load é feita utilizando a função "to_sql".

### **4. API (FastAPI)**

  A tecnologia FastAPI foi utilizada segundo o exigido no PDF. Ela trata alguns dos principais erros de rotas (como o 404). A validação dos parâmetros é feita usando modelos Pydantic. Aqui, eu também utilizei a biblioteca Pandas para algumas operações em DF após criar queries dinâmicas de acesso ao banco de dado baseado nos parâmetros recebidos para retornar a resposta no formato exigido.

##  **Autor**

Desenvolvido por **Pedro de Oliveira Bokel Zborowski**.
