# Use uma imagem base Python oficial
FROM python:3.11-slim

# Instala as dependências de sistema necessárias para o processamento de PDF (Poppler)
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

# Comando de inicialização com timeout de 1 hora (3600 segundos)
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 3600
