## ADDED Requirements

### Requirement: uv as the primary dependency manager
The project SHALL use `uv` as the primary tool for Python environment and dependency management across local development, CI, and Docker builds.

#### Scenario: Developer creates an isolated environment
- **WHEN** a developer runs the documented setup steps
- **THEN** a Python environment is created via `uv`
- **AND** dependencies are installed via `uv sync`

### Requirement: Deterministic installs via lock file
The project SHALL commit `uv.lock` and use frozen sync in CI and Docker builds.

#### Scenario: CI installs dependencies deterministically
- **WHEN** CI installs dependencies
- **THEN** it uses `uv sync --frozen`
- **AND** dependency resolution MUST NOT change during CI runs

### Requirement: Source of truth in pyproject
The project SHALL define direct runtime dependencies and development tooling dependencies in `pyproject.toml`.

#### Scenario: Updating a direct dependency
- **WHEN** maintainers update a direct dependency requirement
- **THEN** they update `pyproject.toml`
- **AND** regenerate the lock file

### Requirement: Optional platform-specific dependency groups
The project SHALL express platform- or hardware-specific dependencies using extras or markers rather than forcing them into the default install set.

#### Scenario: CPU-only environment installation
- **WHEN** dependencies are installed on a CPU-only machine
- **THEN** the default install succeeds without requiring GPU-specific packages
