# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

# Prevents Python from writing .pyc files and enables unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install only what is needed to compile/install packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies into a separate location for clean copying
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    # Number of gunicorn workers (tune via env var on Fly.io)
    WORKERS=2

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Create a non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy application source code
COPY . .

# Create uploads directory and set permissions
RUN mkdir -p uploads/car_images \
    && chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 8000

# Health check hits the dedicated /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

# Run with gunicorn (multi-worker) + uvicorn workers for async support
# WORKERS can be overridden: fly secrets set WORKERS=4
CMD gunicorn main:app \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT} \
    --workers ${WORKERS} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
