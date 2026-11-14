# Contributing to S2S

Thank you for your interest in contributing to S2S (Spec-to-Silicon).

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/<your-username>/Gouthamlabs.git`
3. Read [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) for setup instructions
4. Read [docs/MASTER_SPEC.md](docs/MASTER_SPEC.md) to understand the architecture

## Development Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 22+
- The s2s-eda image: `docker build -t s2s-eda eda/`

### Running Locally
```bash
docker compose up -d --build --wait
```

### Running Tests
```bash
cd backend && python -m pytest -v
cd web && npm run typecheck && npx playwright test
```

## How to Contribute

### Bug Reports
Open an issue with:
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Docker version)

### Feature Requests
Open an issue describing:
- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered

### Pull Requests
1. Create a branch from `main`
2. Make your changes
3. Ensure all tests pass
4. Submit a pull request with a clear description

### Code Style
- Python: follow existing patterns in `backend/`
- TypeScript/React: follow existing patterns in `web/`
- Verilog: follow existing patterns in `designs/`

## Project Rules

- **Trust Layer invariant**: Real EDA tools decide pass/fail — the AI never does
- **Phase gates**: Check `docs/PHASE_GATES.md` before building beyond the current phase
- **Open tools only**: Phase 0 uses exclusively open-source EDA tools and the SKY130 PDK
- **Honest reporting**: All results are reported honestly, including failures

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
