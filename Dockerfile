# Usar imagem oficial do Python
FROM python:3.11-slim

# Evitar que o Python gere arquivos .pyc e garantir logs em tempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Instalar dependências do sistema necessárias para o psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código
COPY . .

# Comando para rodar a aplicação
CMD ["flask", "run", "--host=0.0.0.0"]
