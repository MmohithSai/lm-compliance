# Build from the repo root so rules/ is in the context:
#   docker build -f worker/Dockerfile -t lm-worker .
# Runs on linux/amd64 and linux/arm64 (HF Space free CPU, Oracle ARM).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# opencv (libgl, glib), weasyprint (pango, cairo, gdk-pixbuf), fonts for the PDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgomp1 \
    libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.7.5 /uv /usr/local/bin/uv

WORKDIR /app/worker
COPY worker/pyproject.toml worker/uv.lock ./
RUN uv sync --frozen --no-dev --all-extras --no-install-project

COPY rules /app/rules
COPY worker /app/worker
RUN uv sync --frozen --no-dev --all-extras

CMD ["uv", "run", "--no-sync", "python", "main.py"]
