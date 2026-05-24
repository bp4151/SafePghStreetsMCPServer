# DOMI Obstruction MCP Server — WPRDC data over streaming HTTP
# Multi-stage build: install deps in -dev image, run in minimal Chainguard Python image.
# Server listens on MCP_PORT (default 8000) for streaming HTTP transport (endpoint /mcp).

# ------------------------------------------------------------------------------
# Stage 1: builder — install dependencies into a venv from pyproject.toml
# ------------------------------------------------------------------------------
# How to install dependencies to /app/venv using pyproject.toml:
#   1. Create a venv:    python -m venv /app/venv
#   2. Activate it:      ENV PATH="/app/venv/bin:$PATH"  (or source /app/venv/bin/activate)
#   3. Copy the project: COPY pyproject.toml [and app code] .
#   4. Install project (and its deps from pyproject.toml):
#      pip install --no-cache-dir .
#   Dependencies are read from the [project] dependencies list in pyproject.toml.
#   To add/update deps, edit pyproject.toml and rebuild the image.
# ------------------------------------------------------------------------------
FROM cgr.dev/chainguard/python:latest-dev AS builder

ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/venv/bin:$PATH"

WORKDIR /app

RUN python -m venv /app/venv
COPY pyproject.toml ./
COPY server/__init__.py server/main.py server/format_models.py server/
COPY server/converters/__init__.py server/converters/gpx_converter.py server/converters/
RUN pip install --no-cache-dir .

# ------------------------------------------------------------------------------
# Stage 2: runtime — minimal image with venv and app code only
# ------------------------------------------------------------------------------
FROM cgr.dev/chainguard/python:latest

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PATH="/app/venv/bin:$PATH"

# Streaming HTTP transport: listen on host:port (default 0.0.0.0:8000), endpoint /mcp
ENV MCP_TRANSPORT=streamable-http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000

EXPOSE 8000

COPY server/__init__.py server/main.py server/format_models.py server/
COPY server/converters/__init__.py server/converters/gpx_converter.py server/converters/
COPY --from=builder /app/venv /app/venv

# Optional: limit records ingested on startup (e.g. 5000 for faster startup)
# ENV WPRDC_INGEST_MAX_RECORDS=5000

ENTRYPOINT ["/app/venv/bin/python"]
CMD ["-u", "-m", "server.main"]
