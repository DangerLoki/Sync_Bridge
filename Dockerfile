# ---- Base ----
FROM python:3.12-slim AS base

WORKDIR /app

# Instala dependências do sistema necessárias para compilação de pacotes nativos
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir ".[api,parquet]"

COPY src/ ./src/

# ---- API ----
FROM base AS api

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "src.interfaces.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

# ---- CLI ----
FROM base AS cli

ENTRYPOINT ["python", "-m", "src.interfaces.cli.main"]
CMD ["--help"]
