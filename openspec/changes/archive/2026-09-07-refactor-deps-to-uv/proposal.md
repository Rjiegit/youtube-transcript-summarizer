# Change: Refactor Python dependency management to uv

## Why
目前專案以 `requirements.txt`（多半由 `pip freeze` 產生）作為主要依賴來源，容易出現：
- 依賴集合包含大量 transitive dependencies，難以維護與審查
- 平台差異（Linux/macOS、CPU/GPU）造成安裝不穩定與重現困難
- 安裝速度偏慢，CI/Docker cache 效益有限

導入 `uv` 作為單一標準的環境與依賴管理工具，目標是加速安裝、提升可重現性，並讓本機/CI/Docker 的流程一致。

## What Changes
- 以 `pyproject.toml` 作為依賴「來源真相」（source of truth），並定義 dev 依賴群組
- 新增並提交 `uv.lock`，用於可重現的依賴解析結果
- Makefile / CI 改用 `uv` 安裝與同步依賴（保留必要的相容目標）
- Docker build 改以 `uv sync`（含 cache mount）取代 `pip install -r requirements.txt`
- README 更新安裝與開發流程（以 uv 為主）

## Non-Goals
- 不改動應用功能與 runtime 行為（僅調整依賴管理與開發/CI/Docker 流程）
- 不在此 change 中大幅升級或替換核心依賴（除非 uv 收斂必須）
- 不保留 `requirements.txt` 作為主要流程的一部分（全面以 `pyproject.toml` + `uv.lock` 收斂）

## Impact
- Affected code/tools:
  - `Makefile`：`install`/`freeze` 等 target 調整為 uv 流程
  - `.github/workflows/main.yml`：用 uv 安裝依賴並快取
  - `.docker/Dockerfile`：以 uv 安裝依賴、改善 layer cache
  - `readme.md`：更新開發與部署指引
- Affected artifacts:
  - `pyproject.toml`（新增）
  - `uv.lock`（新增，提交）
  - `requirements.txt`（移除）

## Rollout / Migration
- 開發者：
  - 安裝 uv
  - `uv venv` / `uv sync` 取代 `pip install -r requirements.txt`
- CI / Docker：
  - 以 `uv sync --frozen` 確保 lock file 一致性
  - 不再依賴 `requirements.txt`

## Risks & Mitigations
- 風險：目前 `requirements.txt` 含平台/硬體強耦合套件（例如 `nvidia-*`），uv 收斂後仍需明確區分依賴來源（CPU/GPU、OS）。
  - 緩解：在 `pyproject.toml` 以 extras/markers 分群（例如 `gpu` extra），並讓預設安裝走 CPU-safe 路徑；Docker 依需求選擇安裝 extra。
- 風險：lock 生成需要解析 metadata，可能受網路/鏡像影響。
  - 緩解：CI 以 `uv sync --frozen` 固定版本；必要時使用 cache 與可靠 index 設定。
