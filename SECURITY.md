# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

1. **Do not** open a public issue
2. Email the maintainer directly with details of the vulnerability
3. Include steps to reproduce if possible

You can expect an initial response within 72 hours.

## Scope

This policy covers the S2S framework code, including:
- Backend API and orchestrator (`backend/`)
- Web interface (`web/`)
- EDA tool wrappers (`eda/`)
- Docker and compose configurations

## Security Considerations

- The API does not implement authentication in Phase 0 (local development only)
- API keys for model providers are stored encrypted at rest (Fernet, `var/secrets/`)
- The EDA containers run with Docker socket access for sibling container orchestration
- Never commit `.env` files, API keys, or the `var/` directory
