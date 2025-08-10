import pandas as pd
from sqlalchemy import create_engine
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Conexões com os bancos
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_TRANSACIONAL_NAME = os.getenv('DB_TRANSACIONAL_NAME')
DB_DW_NAME = os.getenv('DB_DW_NAME')

engine_transacional = create_engine(
    f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_TRANSACIONAL_NAME}'
)
engine_dw = create_engine(
    f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DW_NAME}'
)

try:
    print("=== ETL Iniciado ===")

    # Extração (Extract) e transformação (Transform): CSV -> Banco Transacional
    print("Carregando dados no Transacional...")

    # CDA com tratamento de datas inválidas (fonte: /data/001.csv)
    df_cda = pd.read_csv('data/001.csv')
    df_cda = df_cda.drop_duplicates(subset=['numCDA'], keep='first')
    if 'datCadastramento' in df_cda.columns:
        df_cda['datCadastramento'] = pd.to_datetime(df_cda['datCadastramento'], errors='coerce')
        mask = df_cda['datCadastramento'].dt.year < 1980
        df_cda.loc[mask, 'datCadastramento'] = pd.to_datetime('1980-01-01 00:00:00.000')

    # Naturezas da dívida (fonte: /data/002.csv)  mantém apenas colunas do schema
    df_nat_raw = pd.read_csv('data/002.csv')[['idNaturezadivida', 'nomnaturezadivida']]
    df_nat_raw.columns = ['idNaturezaDivida', 'nomNaturezaDivida']  # padroniza nomes como no banco

    # Normaliza IDs duplicados de naturezas
    df_nat_unique = df_nat_raw.drop_duplicates(subset=['nomNaturezaDivida']).reset_index(drop=True)
    df_nat_unique['idNaturezaDivida'] = range(1, len(df_nat_unique) + 1)
    mapa_ids_natureza = pd.merge(
        df_nat_raw, df_nat_unique, on='nomNaturezaDivida', suffixes=('_old', '')
    ).set_index('idNaturezaDivida_old')['idNaturezaDivida'].to_dict()

    # Aplica o mapeamento (ids diferentes que levavam para o mesmo id agora SÃO o mesmo ID)
    if 'idNaturezaDivida' in df_cda.columns:
        df_cda['idNaturezaDivida'] = df_cda['idNaturezaDivida'].map(mapa_ids_natureza)

    df_cda.to_sql('cda', con=engine_transacional, if_exists='append', index=False)
    df_nat_unique.to_sql('naturezas_divida', con=engine_transacional, if_exists='append', index=False)

    # Situações das CDAs (fonte: /data/003.csv), remove duplicados
    df_sit_raw = pd.read_csv('data/003.csv')[['codSituacaoCDA', 'nomSituacaoCDA', 'tipoSituacao']]

    df_sit_raw.to_sql('situacoes_cda', con=engine_transacional, if_exists='append', index=False)

    # Probabilidades (fonte: /data/004.csv), remove coluna desnecessária e duplicados
    df_prob_raw = pd.read_csv('data/004.csv')[['numCDA', 'probRecuperacao']]
    df_prob_raw = df_prob_raw.drop_duplicates(subset=['numCDA'], keep='first')
    df_prob_raw.to_sql('probabilidades', con=engine_transacional, if_exists='append', index=False)

    # CDA_Devedores (fonte: /data/005.csv)  mantém apenas colunas do schema
    df_cdadev = pd.read_csv('data/005.csv')[['numCDA', 'idPessoa']]
    df_cdadev.to_sql('cda_devedores', con=engine_transacional, if_exists='append', index=False)

    # Devedores Pessoa Física (fonte: /data/006.csv)  remove CPFs duplicados e padroniza colunas
    df_pf = pd.read_csv('data/006.csv')[['idpessoa', 'descNome', 'numcpf']]
    df_pf = df_pf.drop_duplicates(subset=['idpessoa'], keep='first')  # evita duplicar PK no transacional
    indices_duplicados = df_pf.duplicated(subset=['numcpf'], keep='first') & df_pf['numcpf'].notna()
    df_pf.loc[indices_duplicados, 'numcpf'] = None
    df_pf.columns = ['idPessoa', 'descNome', 'numCPF']  # padroniza nomes para o schema
    df_pf.to_sql('devedores_pf', con=engine_transacional, if_exists='append', index=False)

    # Devedores Pessoa Jurídica (fonte: /data/007.csv)  remove CNPJs duplicados e padroniza colunas
    df_pj = pd.read_csv('data/007.csv')[['idpessoa', 'descNome', 'numCNPJ']]
    df_pj = df_pj.drop_duplicates(subset=['idpessoa'], keep='first')  # evita duplicar PK no transacional
    indices_duplicados = df_pj.duplicated(subset=['numCNPJ'], keep='first') & df_pj['numCNPJ'].notna()
    df_pj.loc[indices_duplicados, 'numCNPJ'] = None
    df_pj.columns = ['idPessoa', 'descNome', 'numCNPJ']  # padroniza nomes para o schema
    df_pj.to_sql('devedores_pj', con=engine_transacional, if_exists='append', index=False)


    print("Dados carregados no Transacional.")

    # Transformação (Transform) + Carga (Load): Transacional -> DW
    print("Transformando dados e carregando no DW...")

    # Naturezas
    df_nat = pd.read_sql("SELECT * FROM naturezas_divida", engine_transacional).rename(
        columns={'idNaturezaDivida': 'id_natureza', 'nomNaturezaDivida': 'descricao_natureza'}
    )
    df_nat.to_sql('dim_naturezas', con=engine_dw, if_exists='append', index=False)

    # Situações
    df_sit = pd.read_sql("SELECT * FROM situacoes_cda", engine_transacional).rename(
        columns={'codSituacaoCDA': 'id_situacao', 'nomSituacaoCDA': 'descricao_situacao', 'tipoSituacao': 'tipo_situacao'}
    ).drop_duplicates(subset=['id_situacao'])
    df_sit.to_sql('dim_situacoes', con=engine_dw, if_exists='append', index=False)

    # Devedores PF + PJ
    df_pf = pd.read_sql("SELECT * FROM devedores_pf", engine_transacional).rename(
        columns={'idPessoa': 'id_devedor', 'descNome': 'nome', 'numCPF': 'cpf_cnpj'}
    )
    df_pf['tipo_pessoa'] = 'PF'
    df_pj = pd.read_sql("SELECT * FROM devedores_pj", engine_transacional).rename(
        columns={'idPessoa': 'id_devedor', 'descNome': 'nome', 'numCNPJ': 'cpf_cnpj'}
    )
    df_pj['tipo_pessoa'] = 'PJ'
    df_dev = pd.concat([df_pf, df_pj], ignore_index=True).drop_duplicates(subset=['id_devedor'])
    df_dev.to_sql('dim_devedores', con=engine_dw, if_exists='append', index=False)

    # Fatos CDAs
    df_cda = pd.read_sql("SELECT * FROM cda", engine_transacional)
    df_prob = pd.read_sql("SELECT * FROM probabilidades", engine_transacional)
    df_fatos = pd.merge(df_cda, df_prob, on='numCDA', how='left').rename(columns={
    'numCDA': 'num_cda',
    'anoInscricao': 'ano_inscricao',
    'datCadastramento': 'data_cadastramento',
    'DatSituacao': 'data_situacao',
    'ValSaldo': 'valor_saldo',
    'probRecuperacao': 'prob_recuperacao',
    'idNaturezaDivida': 'fk_natureza',
    'codSituacaoCDA': 'fk_situacao'
    })[
    ['num_cda', 'ano_inscricao', 'data_cadastramento', 'data_situacao',
     'valor_saldo', 'prob_recuperacao', 'fk_natureza', 'fk_situacao']
    ] #Remove a coluna codFaseCobrança, pois nao é útil para o DW

    df_fatos = df_fatos[df_fatos['valor_saldo'] >= 0]
    df_fatos.to_sql('fatos_cdas', con=engine_dw, if_exists='append', index=False)

    # Junção CDA - Devedores
    df_junc = pd.read_sql("SELECT * FROM cda_devedores", engine_transacional).rename(
        columns={'numCDA': 'fk_cda', 'idPessoa': 'fk_devedor'}
    ).drop_duplicates(subset=['fk_cda', 'fk_devedor'])
    fatos_cd_keys = pd.read_sql("SELECT num_cda FROM fatos_cdas", engine_dw)
    dev_keys = pd.read_sql("SELECT id_devedor FROM dim_devedores", engine_dw)
    #Filtra quanto fk_cda e fk_devedor não levam a nenhum CDA ou devedor na tabela fato.
    #(provavelmente aconteceu por conta de alguma filtragem anterior, como remover CDAs
    #com saldo negativo ou duplicados
    df_junc = df_junc[
    df_junc['fk_cda'].isin(fatos_cd_keys['num_cda']) &
    df_junc['fk_devedor'].isin(dev_keys['id_devedor'])
    ]
    df_junc.to_sql('jun_cdas_devedores', con=engine_dw, if_exists='append', index=False)

    print("=== ETL concluído com sucesso! ===")

except Exception as e:
    print(f"Erro no ETL: {e}")
    sys.exit(1)