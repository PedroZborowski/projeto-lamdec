# O código é responsável pelo processo ETL ao inserir os dados dos arquivos CSV de entrada no banco de dados.
# A extração de dados é feita com pd.read_csv.
# O tratamento é a etapa mais longa e dinâmica. Alguns dos principais exemplos são as funções de pandas: "rename" para ficar de acordo com as colunas
# do banco de dados, o "concat" para unir as tabelas de devedores tanto de PJ quanto de PF, o "merge" para adicionar da mesma tabela que estavam em
# arquivos diferntes e o não-uso da coluna "stsRecuperacao" no 004.csv, já que ela não será necessária futuramente para a construção dos métodos de busca.
# Por último, o "load" (carregamento) dos dados é feito com o pd.to_sql.

import pandas as pd
from sqlalchemy import create_engine
import os
import sys

def load_data():
    """
    Função principal para executar o pipeline de ETL completo.
    """
    try:
        print("Iniciando pipeline de ETL...")

        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME')
        db_port = os.getenv('DB_PORT')

        if not all([db_user, db_password, db_host, db_name, db_port]):
            print("Erro: Uma ou mais variáveis de ambiente do banco de dados não estão definidas.")
            sys.exit(1)

        connection_string = f'mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
        engine = create_engine(connection_string)

        print("Conexão com o banco de dados estabelecida com sucesso.")

        # Carregar dim_naturezas
        print("Carregando 'dim_naturezas'...")
        df_naturezas = pd.read_csv('data/002.csv')
        df_naturezas = df_naturezas[['idNaturezadivida', 'nomnaturezadivida']].rename(columns={
            'idNaturezadivida': 'id_natureza',
            'nomnaturezadivida': 'descricao_natureza'
        })
        df_naturezas.to_sql('dim_naturezas', con=engine, if_exists='append', index=False)
        print("'dim_naturezas' carregada.")

        # Carregar dim_situacoes
        print("Carregando 'dim_situacoes'...")
        df_situacoes = pd.read_csv('data/003.csv')
        df_situacoes = df_situacoes[['codSituacaoCDA', 'nomSituacaoCDA', 'tipoSituacao']].rename(columns={
            'codSituacaoCDA': 'id_situacao',
            'nomSituacaoCDA': 'descricao_situacao',
            'tipoSituacao': 'tipo_situacao'
        })
        df_situacoes.to_sql('dim_situacoes', con=engine, if_exists='append', index=False)
        print("'dim_situacoes' carregada.")

        # Carregar dim_devedores
        print("Carregando 'dim_devedores'...")
        df_pf = pd.read_csv('data/006.csv')
        df_pf['tipo_pessoa'] = 'PF'
        df_pf.rename(columns={'idpessoa': 'id_devedor', 'descNome': 'nome', 'numcpf': 'cpf_cnpj'}, inplace=True)

        df_pj = pd.read_csv('data/007.csv')
        df_pj['tipo_pessoa'] = 'PJ'
        df_pj.rename(columns={'idpessoa': 'id_devedor', 'descNome': 'nome', 'numCNPJ': 'cpf_cnpj'}, inplace=True)
        
        df_devedores = pd.concat([df_pf, df_pj], ignore_index=True)
        df_devedores = df_devedores[['id_devedor', 'nome', 'cpf_cnpj', 'tipo_pessoa']]
        df_devedores.to_sql('dim_devedores', con=engine, if_exists='append', index=False)
        print("'dim_devedores' carregada.")
        
        print("Carregando 'fatos_cdas'...")
        df_fatos_base = pd.read_csv('data/001.csv')
        df_fatos_prob = pd.read_csv('data/004.csv')


        df_fatos = pd.merge(df_fatos_base, df_fatos_prob, on='numCDA')
        
        df_fatos = df_fatos.rename(columns={
            'numCDA': 'num_cda',
            'anoInscricao': 'ano_inscricao',
            'datCadastramento': 'data_cadastramento',
            'DatSituacao': 'data_situacao',
            'ValSaldo': 'valor_saldo',
            'probRecuperacao': 'prob_recuperacao',
            'idNaturezaDivida': 'fk_natureza',
            'codSituacaoCDA': 'fk_situacao'
        })

        df_fatos_final = df_fatos[['num_cda', 'ano_inscricao', 'data_cadastramento', 'data_situacao', 'valor_saldo', 'prob_recuperacao', 'fk_natureza', 'fk_situacao']]
        df_fatos_final.to_sql('fatos_cdas', con=engine, if_exists='append', index=False)
        print("'fatos_cdas' carregada.")

        print("Carregando 'jun_cdas_devedores'...")
        df_juncao = pd.read_csv('data/005.csv')
        df_juncao = df_juncao[['numCDA', 'idPessoa']].rename(columns={
            'numCDA': 'fk_cda',
            'idPessoa': 'fk_devedor'
        })
        df_juncao.to_sql('jun_cdas_devedores', con=engine, if_exists='append', index=False)
        print("'jun_cdas_devedores' carregada.")

        print("\nPipeline de ETL concluído com sucesso!")

    except Exception as e:
        print(f"Ocorreu um erro durante o pipeline de ETL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    load_data()