from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import ResponseValidationError
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import pandas as pd
import os
from typing import List, Optional
from datetime import date
from dotenv import load_dotenv

load_dotenv()

# Carrega as variáveis de ambiente
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_DW_NAME = os.getenv('DB_DW_NAME')
DB_PORT = os.getenv('DB_PORT')

DATABASE_URL = f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DW_NAME}'

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modelos de dados (pydantic)
# Define a estrutura da resposta JSON para garantir o formato correto.
# Essa é a sessão do código que lida com type errors (internamente pelo pydantic)

class CdaResponse(BaseModel):
    numCDA: str
    valor_saldo_atualizado: float
    qtde_anos_idade_cda: int
    agrupamento_situacao: int
    natureza: str
    score: float

    # Configuração para permitir que o Pydantic leia dados de objetos que não são dicts (como os resultados do SQLAlchemy)
    class Config:
        from_attributes = True

class DetalhesResponse(BaseModel):
    name: str
    tipo_pessoa: str
    cpf_cnpj: Optional[str] = Field(alias="CPF/CNPJ")

    class Config:
        from_attributes = True

class DistribuicaoResponse(BaseModel):
    name: str
    em_cobranca: float = Field(alias = "Em cobranca")
    Cancelada: float
    Quitada: float

    class Config:
        from_attributes = True

class InscricoesResponse(BaseModel):
    ano: int
    Quantidade: int

    class Config:
        from_attributes = True

class MontanteResponse(BaseModel):
    Percentual: int
    IPTU: float
    ISS: float
    Taxas: float
    Multas: float
    ITBI: float

    class Config:
        from_attributes = True

class QtdeResponse(BaseModel):
    name: str
    Quantidade: int

    class Config:
        from_attributes = True

class SaldoResponse(BaseModel):
    name: str
    Saldo: float

    class Config:
        from_attributes = True

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
    id_devedor: Optional[int] = None,    #Por mais que não esteja especificado no enunciado, detalhes_devedor parece
    db: Session = Depends(get_db) #se referir a um devedor especifico, portanto, faria sentido poder achá-lo a partir de seu id_devedor.
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
    if id_devedor is not None:
        query_str += " WHERE j.fk_devedor = :id_devedor"

    try:
        results = db.execute(text(query_str), {"id_devedor": id_devedor}).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar o banco de dados: {e}")
    return results

@app.get("/resumo/distribuicao_cdas", response_model=List[DistribuicaoResponse])
def distribuicao_cdas(
    db: Session = Depends(get_db)
):
    #A lógica desse query é setar como 1 e passar para o count, que por padrão ignora os valores Null (que os condicionais
    #atribuem automaticamente quando a condição não é cumprida), e, portanto, só conta nas colunas especificadas. *100/total é simplesmente
    #conversão para porcentagem.
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
def inscricoes(
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
def montante_acumulado(
    db: Session = Depends(get_db)
):
    #Essa query prepara uma tabela para ser ainda mais processada com Pandas e gerar o resultado esperado.
    #Primeiro, agrupamos as descricao_natureza de acordo (englobamos todos os IPTU em um por exemplo).
    #Depois, usamos NTILE(100) para criar 100 partições nos grupos especificados, ordenados por saldo (assim,
    #cada partição é um percentil.
    query_str = """
        SELECT
            CASE
                WHEN d.descricao_natureza LIKE 'IPTU%' THEN 'IPTU'
                WHEN d.descricao_natureza LIKE 'ISS%' THEN 'ISS'
                WHEN d.descricao_natureza LIKE 'Taxa%' THEN 'Taxas'
                WHEN d.descricao_natureza LIKE 'Multa%' THEN 'Multas'
                WHEN d.descricao_natureza LIKE 'ITBI%' THEN 'ITBI'
            END AS tipo_tributo,
            f.valor_saldo,
            NTILE(100) OVER (PARTITION BY 
            CASE
                WHEN d.descricao_natureza LIKE 'IPTU%' THEN 'IPTU'
                WHEN d.descricao_natureza LIKE 'ISS%' THEN 'ISS'
                WHEN d.descricao_natureza LIKE 'Taxa%' THEN 'Taxas'
                WHEN d.descricao_natureza LIKE 'Multa%' THEN 'Multas'
                WHEN d.descricao_natureza LIKE 'ITBI%' THEN 'ITBI'
            END
            ORDER BY f.valor_saldo) AS percentil
        FROM 
            fatos_cdas f
        JOIN 
            dim_naturezas d ON f.fk_natureza = d.id_natureza
        WHERE 
            d.descricao_natureza LIKE 'IPTU%' OR
            d.descricao_natureza LIKE 'ISS%' OR
            d.descricao_natureza LIKE 'Taxa%' OR
            d.descricao_natureza LIKE 'Multa%' OR 
            d.descricao_natureza LIKE 'ITBI%'
    """

    try:
        df = pd.read_sql(text(query_str), db.bind)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar o banco de dados: {e}")


    if df.empty:
        return []

    #Agrupamos o df por tipo do tributo e calculamos a soma do saldo para cada um
    total_por_tributo = df.groupby('tipo_tributo')['valor_saldo'].sum()

    #Agrupamos por tipo e percentil e calculamos a soma de cada um. reset_index serve para criar índices novos e facilitar a manipulação.
    soma_por_percentil = df.groupby(['tipo_tributo', 'percentil'])['valor_saldo'].sum().reset_index()

    #Isso acumula a soma cumulativa (no percentil 1, é o valor ATÉ o 1. no 5, é ATÉ o 5 e assim em diante.)
    soma_por_percentil['valor_acumulado'] = soma_por_percentil.groupby('tipo_tributo')['valor_saldo'].cumsum()

    #Apply aplica a função lambda em cada linha row. Isso simplesmente calcula o percentual acumulado.
    soma_por_percentil['percentual_acumulado'] = soma_por_percentil.apply(
        lambda row: (row['valor_acumulado'] / total_por_tributo[row['tipo_tributo']]) * 100,
        axis=1
    )

    #Aqui, filtramos com indexação booleana. A lista de dentro é uma lista de verdadeiros ou falsos, e usar isso para indexar retorna
    #um DF apenas com as linhas que eram verdadeiras na lista. Usamos isin para checar se estava entre os percentis desejados.
    percentis_desejados = [1] + list(range(5, 101, 5))
    df_filtrado = soma_por_percentil[soma_por_percentil['percentil'].isin(percentis_desejados)]

    #pivot_table serve para "pivotear" a tabela. Da maneira como está feito, serve basicamente para
    #trocar as linhas pelas colunas. O reset_index faz com que o percentil não seja o próprio index e se torne
    #uma coluna.
    df_pivot = df_filtrado.pivot_table(
        index='percentil', 
        columns='tipo_tributo',
        values='percentual_acumulado'
    ).reset_index()
    
    df_pivot = df_pivot.rename(columns={'percentil': 'Percentual'})

    for tributo in ['IPTU', 'ISS', 'Taxas', 'Multas', 'ITBI']:
        if tributo not in df_pivot.columns:
            df_pivot[tributo] = 0.0

    results = df_pivot.fillna(0.0).to_dict(orient='records')

    return results

@app.get("/resumo/quantidade_cdas", response_model=List[QtdeResponse])
def quantidade_cdas(
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
def saldo_cdas(
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