# s2s web image: the Live Office (M0.4), a Next.js standalone server on :3000.
# Build from the repo root (it reads config/management.yaml to seat the org):
#   docker build -f web/Dockerfile -t s2s-web .
# Behind a TLS-intercepting proxy, pass its CA as an optional build secret (not stored):
#   docker build --secret id=proxy_ca,src=/path/to/ca.crt -f web/Dockerfile -t s2s-web .
# The browser talks to the API at <page host>:8000 unless NEXT_PUBLIC_S2S_API is set at build.
FROM node:22.20.0-slim AS build
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN --mount=type=secret,id=proxy_ca,required=false \
    if [ -s /run/secrets/proxy_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/proxy_ca; fi; \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm ci --no-audit --no-fund
COPY config /app/config
COPY web ./
ARG NEXT_PUBLIC_S2S_API=
ENV NEXT_PUBLIC_S2S_API=$NEXT_PUBLIC_S2S_API NEXT_TELEMETRY_DISABLED=1 S2S_STANDALONE=1
RUN npm run build

FROM node:22.20.0-slim
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=0.0.0.0 PORT=3000
COPY --from=build /app/web/.next/standalone ./
COPY --from=build /app/web/.next/static ./.next/static
USER node
EXPOSE 3000
CMD ["node", "server.js"]
