FROM python:3.12-slim

# Install system dependencies for CasFinder
RUN apt-get update && apt-get install -y \
    hmmer \
    prodigal \
    git \
    && rm -rf /var/lib/apt/lists/*

# Download CasFinder models
RUN git clone https://github.com/macsy-models/CasFinder /opt/casfinder-models

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render requires binding to 0.0.0.0 and the PORT env var (default 10000)
CMD ["bash", "-lc", "gunicorn -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 120"]
