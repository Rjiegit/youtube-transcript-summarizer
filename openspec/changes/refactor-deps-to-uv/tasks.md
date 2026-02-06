## 1. Proposal approval gate
- [ ] Review this change proposal and confirm scope: full convergence to `uv` (local + CI + Docker + Makefile + README)

## 2. Dependency source of truth
- [ ] Add `pyproject.toml` with:
  - [ ] `project.requires-python` set to Python 3.11
  - [ ] `project.dependencies` capturing direct/runtime deps (not the full freeze)
  - [ ] Dev dependency group containing lint/test tools used in CI (e.g. `flake8`, `pytest`, `pytest-mock` if still needed)
- [ ] Decide strategy for platform-specific deps:
  - [ ] Option A: default CPU-safe deps, with `gpu` extra for CUDA packages
  - [ ] Option B: keep current behavior pinned for Docker only, and document limitations

## 3. Locking & reproducibility
- [ ] Generate and commit `uv.lock`

## 4. Update developer workflows
- [ ] Update `Makefile` targets:
  - [ ] `install` uses `uv sync` (and still installs `yt-dlp` as needed)
  - [ ] `freeze` becomes `uv lock` + (optional) `uv export`
- [ ] Update `readme.md` to uv-first instructions (local + Docker)

## 5. Update CI
- [ ] Update `.github/workflows/main.yml`:
  - [ ] Install uv
  - [ ] Cache uv downloads (and/or Python build cache)
  - [ ] `uv sync --frozen` for deterministic installs
  - [ ] Keep lint + unittest steps as-is, but executed within uv environment

## 6. Update Docker build
- [ ] Update `.docker/Dockerfile`:
  - [ ] Install uv
  - [ ] Copy `pyproject.toml` + `uv.lock` for cacheable dependency layer
  - [ ] `uv sync --frozen` during build with cache mounts

## 7. Verification
- [ ] `make test` passes locally using uv environment
- [ ] Docker build succeeds (api + streamlit services)
- [ ] CI pipeline passes with uv-based install
