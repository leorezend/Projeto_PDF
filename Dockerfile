# Use uma imagem base Python oficial
FROM python:3.11-slim

# Instala as dependências de sistema necessárias para o processamento de PDF (Poppler)
# O Poppler é essencial para o pdfplumber/pdfminer
RUN apt-get update && \
    apt-get install -y poppler-utils && \
    rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia o arquivo de requisitos e instala as dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código
COPY . .

# Expõe a porta que o Gunicorn irá usar
EXPOSE 10000

# O Render usa a variável de ambiente PORT, mas o Gunicorn precisa de um valor padrão
# O Render irá injetar a variável PORT, mas vamos usar o CMD do Procfile
# O Render detectará automaticamente que é um serviço Docker se o Dockerfile estiver presente.

# Comando de inicialização (igual ao seu Procfile, mas sem o 'web: ')
# O Render irá usar este comando se não houver um Procfile, mas é bom mantê-lo
# para garantir que o Gunicorn use o timeout de 1 hora (3600 segundos)
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 3600
