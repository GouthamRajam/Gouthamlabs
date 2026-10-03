# s2s backend image: API server, orchestrator and DB migrations (M0.3).
# Build from the repo root: docker build -f backend/Dockerfile -t s2s-backend .
# Behind a TLS-intercepting proxy, pass its CA as an optional build secret (not stored):
#   docker build --secret id=proxy_ca,src=/path/to/ca.crt -f backend/Dockerfile -t s2s-backend .
FROM python:3.11.15-slim
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN --mount=type=secret,id=proxy_ca,required=false \
    if [ -s /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    pip install --no-cache-dir -r requirements.txt
COPY config /app/config
COPY backend/alembic.ini ./
COPY backend/s2s ./s2s
ENV PYTHONUNBUFFERED=1 S2S_CONFIG_DIR=/app/config
CMD ["uvicorn", "s2s.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
