# ==============================================================================
# VAULTBASIS EDGE RUNTIME CONTAINER (MMP-1 PREVIEW)
# Conforms to PRD §6.1, §18.1, §21.1 (Zero Token Bleed / Zero Transaction Egress)
# ==============================================================================

FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final minimal execution stage
FROM python:3.11-slim AS runner

# Security hardening: create non-root service user
RUN groupadd -g 10001 vaultbasis && \
    useradd -u 10001 -g vaultbasis -s /bin/false -M vaultbasis

# Working directory
WORKDIR /app

# Copy python dependencies from builder
COPY --from=builder /root/.local /home/vaultbasis/.local

# Copy application code and schemas
COPY edge /app/edge
COPY schemas /app/schemas
COPY apps /app/apps

# Ensure data directory exists with strict permissions for non-root user
RUN mkdir -p /app/data /app/data/keys && \
    chown -R vaultbasis:vaultbasis /app /home/vaultbasis && \
    chmod 700 /app/data /app/data/keys

ENV PATH=/home/vaultbasis/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VAULTBASIS_DATA_DIR=/app/data \
    VAULTBASIS_KEY_DIR=/app/data/keys \
    VAULTBASIS_HOST=0.0.0.0 \
    VAULTBASIS_PORT=8000

# Run as unprivileged user
USER vaultbasis

# Expose internal Edge port
EXPOSE 8000

# Health check verifies local health endpoint only
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')" || exit 1

ENTRYPOINT ["python3", "-m", "uvicorn", "edge.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
