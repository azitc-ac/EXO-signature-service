FROM python:3.11-slim AS base

WORKDIR /app

# System deps for curl (healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY app/ .

# Non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 587 8080

VOLUME ["/app/templates", "/app/certs"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "main.py"]
