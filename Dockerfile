# Research image: Python 3.12, hashed [all] extras, CPU torch + faiss-cpu.
# Build on amd64 (GitHub runners / most servers):
#   docker build --platform linux/amd64 -t rageval:0.2.1 .
# The lock file is manylinux x86_64. Apple Silicon hosts need that platform flag.
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    RAGEVAL_RUNS_DIR=/app/experiments/runs \
    RAGEVAL_DATA_DIR=/app/data

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-lock-all.txt pyproject.toml README.md LICENSE ./
COPY rageval ./rageval
COPY data ./data
COPY configs ./configs
COPY reports ./reports
COPY scripts ./scripts
COPY experiments/runs/.gitkeep experiments/runs/.gitkeep

RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --require-hashes -r requirements-lock-all.txt \
    && pip install --no-cache-dir --no-deps .

RUN useradd --create-home --uid 1000 rageval \
    && mkdir -p /app/experiments/runs \
    && chown -R rageval:rageval /app

USER rageval
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/health', timeout=4)"
CMD ["rageval", "serve", "--host", "0.0.0.0", "--port", "8000"]
