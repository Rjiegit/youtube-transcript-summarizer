## 1. Proposal approval gate
- [x] Review this change proposal and confirm scope: full convergence to `uv` (local + CI + Docker + Makefile + README)

## 2. Dependency source of truth
- [x] Add `pyproject.toml` with the current supported Python version, direct runtime dependencies, and the development dependency group.
- [x] Keep platform-specific inference dependencies compatible with the documented local and Docker workflows.

## 3. Locking & reproducibility
- [x] Generate and commit `uv.lock`

## 4. Update developer workflows
- [x] Update `Makefile` targets to use `uv sync` while preserving the yt-dlp installer.
- [x] Update `readme.md` to uv-first instructions (local + Docker)

## 5. Update CI
- [x] Update `.github/workflows/main.yml` to install uv, sync deterministically, and run lint/tests in the uv environment.

## 6. Update Docker build
- [x] Update `.docker/Dockerfile` to install uv and use `pyproject.toml` plus `uv.lock` for a cacheable deterministic build.

## 7. Verification
- [x] Tests run locally using the uv environment
- [x] Docker services build with the uv-based dependency layer
- [x] CI uses the uv-based install and verification flow
