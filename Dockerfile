#Imagem base usada na construção: python na versão 3.9-slim
FROM python:3.9-slim

#Entramos na pasta app criada no ambiente Docker
WORKDIR /app

#Copiamos nossos requirements para depois instalá-los usando pip install.
#Isso acontece antes de copiar o projeto todo porque o Docker detecta mudanças
#E só reconstrói a partir da imagem se ela mudou. Para não executar pip install
#Quando QUALQUER arquivo mudar, fazemos isso antes de copiar o resto.
COPY ./api/requirements.txt /app/api/requirements.txt
RUN pip install --no-cache-dir -r /app/api/requirements.txt

#Colocamos nosso projeto na pasta app riada no ambiente Docker
COPY . /app

#Damos permissão ao wait-for-it (script de espera do BD) e 
#definimos o comando padrão como o de hostar o servidor usando uvicorn, em 0.0.0.0:8000 (que vai ser mapeado
#internamente pelo nginx para a porta http padrão na nossa máquina). Repare que, no docker-compose,
#o serviço de ETL substitui esse comando pelo seu comando de execução.
RUN chmod +x /app/wait-for-it.sh

#Precisamos rodar o uvicorn em 0.0.0.0 para ele conseguir receber requisições dos outros containers
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]