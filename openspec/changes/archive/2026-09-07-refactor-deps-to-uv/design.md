# Design: uv 收斂策略

## 目標
- 讓本機、CI、Docker 都用同一套依賴/環境管理方式（uv）
- 以 lock file 提升可重現性（`uv.lock` committed）
- 將依賴定義從「完整 freeze」轉為「直接依賴 + 分群 extras」，減少平台耦合與維護成本

## 依賴定義
### Source of truth
- `pyproject.toml`：
  - `project.dependencies`：僅放 runtime 直接依賴（例如 `fastapi`, `uvicorn`, `streamlit`, `openai`, `google-generativeai`, `faster-whisper` 等）
  - `dependency-groups`（或 uv 支援的 dev group）：放 lint/test/開發工具（例如 `flake8`, `pytest`, `pytest-mock`）

### 平台/硬體依賴
目前 `requirements.txt` 內包含 `nvidia-*`（CUDA runtime）類套件，這對：
- macOS/CPU-only 安裝不友善
- CI（ubuntu-latest）也可能因缺少相容 wheel 而不穩

建議做法：
- 預設安裝走 CPU-safe 的依賴集合
- 以 extras 分群：例如 `gpu` extra 才安裝 CUDA 相關或 GPU 專用 runtime
- Docker（若需要 GPU）再用 `uv sync --extra gpu`

> 註：是否保留 GPU 相關依賴為「預設」將在實作前先確認目前部署目標（CPU-only vs GPU）。

## Lock 與相容輸出
- `uv.lock`：作為唯一鎖定來源，CI/Docker 均以 `--frozen` 確保一致
- `requirements.txt`：不再使用（全面以 `pyproject.toml` + `uv.lock` 收斂）

## CI / Docker
- CI：
  - 安裝 uv
  - `uv sync --frozen`（dev group included）
- Docker：
  - 先 copy `pyproject.toml` + `uv.lock` 以建立可 cache 的依賴 layer
  - `uv sync --frozen` with cache mount (`/root/.cache/uv`)
