from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import ResponseValidationError
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import os
from typing import List, Optional
from datetime import date
from dotenv import load_dotenv

load_dotenv()

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
    cpf_cnpj: Optional[str] = Field(alias="CPF/CNPJ")

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
    Quantidade: int

    class Config:
        orm_mode = True

class SaldoResponse(BaseModel):
    name: str
    Saldo: float

    class Config:
        orm_mode = True

# APLICAÇÃO FASTAPI E ENDPOINT

app = FastAPI()

#Essa função serve para retornar erros internos de servidor (código 500) mais detalhados para facilitar depuração de erros.
@app.exception_handler(ResponseValidationError)
async def validation_exception_handler(request: Request, exc: ResponseValidationError):
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocorreu um erro interno ao validar os dados de resposta.", "validation_errors": exc.errors()},
    )

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

    #Verificação dos parâmetros de intervalo e paginação
    if minSaldo is not None and maxSaldo is not None and minSaldo > maxSaldo:
        raise HTTPException(
            status_code=400,
            detail="Parâmetro inválido: O saldo mínimo (minSaldo) não pode ser maior que o saldo máximo (maxSaldo)."
        )
    
    if minAno is not None and maxAno is not None and minAno > maxAno:
        raise HTTPException(
            status_code=400,
            detail="Parâmetro inválido: O ano mínimo (minAno) não pode ser maior que o ano máximo (maxAno)."
        )
    
    if sort_by not in ["ano", "valor"]:
        raise HTTPException(
            status_code=400,
            detail="Parâmetro inválido: 'sort_by' deve ser 'ano' ou 'valor'."
        )

    if sort_order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=400,
            detail="Parâmetro inválido: 'sort_order' deve ser 'asc' ou 'desc'."
        )
    
    if skip < 0:
        raise HTTPException(
            status_code=400,
            detail="Parâmetro inválido: 'skip' não pode ser um número negativo."
        )
    
    if limit <= 0:
        raise HTTPException(
            status_code=400,
            detail="Parâmetro inválido: 'limit' deve ser um número positivo."
        )

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
        cda_data = dict(row._mapping)

        cda_data['numCDA'] = str(cda_data['numCDA'])
        
        # Calcula a idade da CDA
        cda_data['qtde_anos_idade_cda'] = current_year - cda_data.get('ano_inscricao', current_year)
        
        # Remove a coluna de ano que não faz parte do modelo de resposta final
        del cda_data['ano_inscricao']

        final_response.append(cda_data)

    return final_response

@app.get("/cda/detalhes_devedor", response_model=List[DetalhesResponse])
def detalhes_devedor(
    db: Session = Depends(get_db)
):
    #DISTINCT para não repetir devedores.
    query_str = """
        SELECT DISTINCT
           d.nome AS name,
           d.tipo_pessoa,
           d.cpf_cnpj AS `CPF/CNPJ`
        FROM jun_cdas_devedores j
        JOIN dim_devedores d ON j.fk_devedor = d.id_devedor
    """
    try:
        results = db.execute(text(query_str)).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar o banco de dados: {e}")
    return results

@app.get("/resumo/distribuicao_cdas", response_model=List[DistribuicaoResponse])
def detalhes_devedor(
    db: Session = Depends(get_db)
):
    query_str = """
        SELECT
            d.descricao_natureza AS name,
            (COUNT(CASE 
                WHEN s.descricao_situacao LIKE 'Cobrança%' OR s.descricao_situacao IN ('Parcelada', 'Leilão', 'Arrematação', 'Negociada', 'Parcelamento Irregular') 
                THEN 1 
             END) * 100.0 / COUNT(*)) AS `Em cobranca`,
            (COUNT(CASE 
                WHEN s.descricao_situacao LIKE 'Cancelada%' OR s.descricao_situacao = 'Migracao Cancelamento'
                THEN 1 
             END) * 100.0 / COUNT(*)) AS `Cancelada`,
            (COUNT(CASE 
                WHEN s.descricao_situacao LIKE 'Paga%' OR s.descricao_situacao = 'Migracao Pagos'
                THEN 1 
             END) * 100.0 / COUNT(*)) AS `Quitada`
        FROM 
            fatos_cdas f
        JOIN 
            dim_naturezas d ON f.fk_natureza = d.id_natureza
        JOIN 
            dim_situacoes s ON f.fk_situacao = s.id_situacao
        GROUP BY 
            d.descricao_natureza
        ORDER BY
            d.descricao_natureza;
    """

    try:
        results = db.execute(text(query_str)).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar o banco de dados: {e}")
    return results

@app.get("/resumo/inscricoes", response_model=List[InscricoesResponse])
def detalhes_devedor(
    db: Session = Depends(get_db)
):
    query_str = """
        SELECT
            f.ano_inscricao AS ano,
            COUNT(*) AS Quantidade
        FROM 
            fatos_cdas f
        GROUP BY 
            f.ano_inscricao
        ORDER BY
            f.ano_inscricao;
    """

    try:
        results = db.execute(text(query_str)).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar o banco de dados: {e}")
    return results

@app.get("/resumo/montante_acumulado", response_model=List[MontanteResponse])
def detalhes_devedor(
    db: Session = Depends(get_db)
):
    query_str = """
        SELECT
            f.ano_inscricao AS ano,
            COUNT(*) AS Quantidade
        FROM 
            fatos_cdas f
        GROUP BY 
            f.ano_inscricao
        ORDER BY
            f.ano_inscricao;
    """

    try:
        results = db.execute(text(query_str)).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar o banco de dados: {e}")
    return results

@app.get("/resumo/quantidade_cdas", response_model=List[QtdeResponse])
def detalhes_devedor(
    db: Session = Depends(get_db)
):
    query_str = """
        SELECT
            d.descricao_natureza AS name,
            COUNT(*) AS Quantidade
        FROM 
            fatos_cdas f
        JOIN
            dim_naturezas d ON f.fk_natureza = d.id_natureza
        GROUP BY 
            d.descricao_natureza
        ORDER BY
            d.descricao_natureza;
    """

    try:
        results = db.execute(text(query_str)).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar o banco de dados: {e}")
    return results

@app.get("/resumo/saldo_cdas", response_model=List[SaldoResponse])
def detalhes_devedor(
    db: Session = Depends(get_db)
):
    query_str = """
        SELECT
            d.descricao_natureza AS name,
            SUM(f.valor_saldo) AS Saldo
        FROM 
            fatos_cdas f
        JOIN
            dim_naturezas d ON f.fk_natureza = d.id_natureza
        GROUP BY 
            d.descricao_natureza
        ORDER BY
            d.descricao_natureza;
    """

    try:
        results = db.execute(text(query_str)).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar o banco de dados: {e}")
    return results