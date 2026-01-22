FROM python:3.12-slim

# System deps for CasFinder: hmmer (hmmsearch), prodigal, git
RUN apt-get update && apt-get install -y \
    hmmer \
    prodigal \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python deps first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download CasFinder models
RUN git clone https://github.com/macsy-models/CasFinder /opt/casfinder-models

# Copy app
COPY . .

# Where we will store models in a standard place
ENV MACSY_MODELS_DIR=/usr/local/share/macsyfinder/models
RUN mkdir -p ${MACSY_MODELS_DIR} && cp -r /opt/casfinder-models/* ${MACSY_MODELS_DIR}/

# Render start
CMD ["bash", "-lc", "gunicorn -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 120"]
