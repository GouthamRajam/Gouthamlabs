# s2s backend image: API server, orchestrator and DB migrations (M0.3; M0.5-M0.7 agents).
# Build from the repo root: docker build -f backend/Dockerfile -t s2s-backend .
# Behind a TLS-intercepting proxy, pass its CA as an optional build secret (not stored):
#   docker build --secret id=proxy_ca,src=/path/to/ca.crt -f backend/Dockerfile -t s2s-backend .
# The orchestrator runs every EDA tool in the separate s2s-eda image (eda/), as a sibling container
# through the host's Docker socket, so this image carries the docker CLI (pinned, checksum-verified).
FROM python:3.11.15-slim
ARG DOCKER_CLI_VERSION=27.3.1
ARG DOCKER_CLI_SHA256=9b4f6fe406e50f9085ee474c451e2bb5adb119a03591f467922d3b4e2ddf31d3
RUN --mount=type=secret,id=proxy_ca,required=false \
    python - <<EOF
import hashlib, io, os, ssl, tarfile, urllib.request
ca = "/run/secrets/proxy_ca"
ctx = ssl.create_default_context(cafile=ca) if os.path.exists(ca) and os.path.getsize(ca) else None
url = "https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_CLI_VERSION}.tgz"
data = urllib.request.urlopen(url, context=ctx).read()
digest = hashlib.sha256(data).hexdigest()
assert digest == "${DOCKER_CLI_SHA256}", f"docker CLI checksum mismatch: {digest}"
tarfile.open(fileobj=io.BytesIO(data)).extract("docker/docker", "/tmp")
os.replace("/tmp/docker/docker", "/usr/local/bin/docker")
os.chmod("/usr/local/bin/docker", 0o755)
EOF
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN --mount=type=secret,id=proxy_ca,required=false \
    if [ -s /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    pip install --no-cache-dir -r requirements.txt
# Repo files the agents read at run time (paths are relative to the repo root, here /app)
COPY config /app/config
COPY eda/versions.lock /app/eda/versions.lock
COPY designs /app/designs
COPY docs/coding_standard.md /app/docs/coding_standard.md
COPY backend/tests/platform/m05_fixtures /app/backend/tests/platform/m05_fixtures
COPY backend/tests/platform/m06_fixtures /app/backend/tests/platform/m06_fixtures
COPY backend/alembic.ini ./
COPY backend/s2s ./s2s
COPY backend/scripts ./scripts
ENV PYTHONUNBUFFERED=1 S2S_CONFIG_DIR=/app/config
CMD ["uvicorn", "s2s.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
