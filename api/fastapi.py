from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import os
from typing import List, Optional
from datetime import date

# CONFIGURAÇÃO E CONEXÃO COM O BANCO DE DADOS

# Carrega as variáveis de ambiente
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_PORT = os.getenv('DB_PORT')

DATABASE_URL = f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# Cria o "motor" de conexão do SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Função para obter uma sessão do banco de dados para cada requisição
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# MODELOS DE DADOS (PYDANTIC)
# Define a estrutura da resposta JSON para garantir o formato correto.

class CdaResponse(BaseModel):
    numCDA: str
    valor_saldo_atualizado: float
    qtde_anos_idade_cda: int
    agrupamento_situacao: int
    natureza: str
    score: float

    # Configuração para permitir que o Pydantic leia dados de objetos que não são dicts (como os resultados do SQLAlchemy)
    class Config:
        orm_mode = True

class DetalhesResponse(BaseModel):
    name: str
    tipo_pessoa: str
    cpf_cnpj: str = Field(alias="CPF/CNPJ")

    class Config:
        orm_mode = True

class DistribuicaoResponse(BaseModel):
    name: str
    em_cobranca: float = Field(alias = "Em cobranca")
    Cancelada: float
    Quitada: float

    class Config:
        orm_mode = True

class InscricoesResponse(BaseModel):
    ano: int
    Quantidade: int

    class Config:
        orm_mode = True

class MontanteResponse(BaseModel):
    Percentual: int
    IPTU: float
    ISS: float
    Taxas: float
    Multas: float
    ITBI: float

    class Config:
        orm_mode = True

class QtdeResponse(BaseModel):
    name: str
    Quantidade: str

    class Config:
        orm_mode = True

class SaldoResponse(BaseModel):
    name: str
    Saldo: float

    class Config:
        orm_mode = True

# APLICAÇÃO FASTAPI E ENDPOINT

app = FastAPI()

@app.get("/cda/search", response_model=List[CdaResponse])
def search_cda(
    # Parâmetros de filtro opcionais
    numCDA: Optional[str] = None,
    minSaldo: Optional[float] = None,
    maxSaldo: Optional[float] = None,
    minAno: Optional[int] = None,
    maxAno: Optional[int] = None,
    natureza: Optional[str] = None,
    agrupamento_situacao: Optional[int] = None,
    # Parâmetros de ordenação e paginação com valores padrão
    sort_by: str = "ano",
    sort_order: str = "asc",
    skip: int = 0,
    limit: int = 100,
    # Injeção de dependência da sessão do banco de dados
    db: Session = Depends(get_db)
):
    """
    Busca e filtra CDAs com base em múltiplos critérios, com ordenação e paginação.
    """
    # Lógica de Construção da Query Dinâmica

    #Base da query SQL
    query_str = """
        SELECT 
            f.num_cda AS numCDA,
            f.valor_saldo AS valor_saldo_atualizado,
            f.ano_inscricao,
            f.fk_situacao AS agrupamento_situacao,
            d.descricao_natureza AS natureza,
            f.prob_recuperacao AS score
        FROM fatos_cdas f
        JOIN dim_naturezas d ON f.fk_natureza = d.id_natureza
    """

    # Lista para armazenar as cláusulas WHERE e dicionário para os parâmetros
    where_clauses = []
    params = {}

    # Adiciona filtros à query se os parâmetros forem fornecidos
    if numCDA:
        where_clauses.append("f.num_cda = :numCDA")
        params["numCDA"] = numCDA
    if minSaldo is not None:
        where_clauses.append("f.valor_saldo >= :minSaldo")
        params["minSaldo"] = minSaldo
    if maxSaldo is not None:
        where_clauses.append("f.valor_saldo <= :maxSaldo")
        params["maxSaldo"] = maxSaldo
    if minAno is not None:
        where_clauses.append("f.ano_inscricao >= :minAno")
        params["minAno"] = minAno
    if maxAno is not None:
        where_clauses.append("f.ano_inscricao <= :maxAno")
        params["maxAno"] = maxAno
    if natureza:
        where_clauses.append("d.descricao_natureza LIKE :natureza")
        params["natureza"] = f"%{natureza}%"
    if agrupamento_situacao is not None:
        where_clauses.append("f.fk_situacao = :agrupamento_situacao")
        params["agrupamento_situacao"] = agrupamento_situacao

    # Junta as cláusulas WHERE, se houver alguma
    if where_clauses:
        query_str += " WHERE " + " AND ".join(where_clauses)

    # Lógica de Ordenação
    # Valida os inputs para evitar SQL Injection
    order_column = "f.ano_inscricao" if sort_by == "ano" else "f.valor_saldo"
    order_direction = "DESC" if sort_order == "desc" else "ASC"
    query_str += f" ORDER BY {order_column} {order_direction}"

    # Lógica de Paginação
    query_str += " LIMIT :limit OFFSET :skip"
    params["limit"] = limit
    params["skip"] = skip

    # Executa a query final
    try:
        results = db.execute(text(query_str), params).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar o banco de dados: {e}")

    # Resultado
    final_response = []
    current_year = date.today().year
    for row in results:
        # Cria um dicionário a partir do resultado para manipulação
        cda_data = dict(row)
        
        # Calcula a idade da CDA
        cda_data['qtde_anos_idade_cda'] = current_year - cda_data.get('ano_inscricao', current_year)
        
        # Remove a coluna de ano que não faz parte do modelo de resposta final
        del cda_data['ano_inscricao']

        final_response.append(cda_data)

    return final_response

@app.get("/cda/detalhes_devedor", response_model=List[DetalhesResponse])
def detalhes_devedor(
    numCDA: Optional[str] = None, # Não exigido, porém, faz sentido conseguir encontrar um devedor específico pelo CDA
    db: Session = Depends(get_db)
):
    #DISTINCT para não repetir devedores.
    query_str = """
        SELECT DISTINCT
           d.nome AS name
           d.tipo_pessoa
           d.cpf_cnpj AS `CPF/CNPJ`  
        FROM jun_cdas_devedores j
        JOIN dim_devedores d ON j.fk_devedor = d.id_devedor
    """

    where_clauses = []
    params = {}

    if numCDA:
        where_clauses.append("j.fk_cda = :numCDA")
        params["numCDA"] = numCDA

    if where_clauses:
        query_str += " WHERE " + " AND ".join(where_clauses)

    results = db.execute(text(query_str), params).fetchall()
    return results