# 選擇基礎映像
FROM python:3.11-slim

# 安裝必要的程式和 pip cache 優化
RUN apt update && \
    apt install -y ffmpeg && \
    apt install -y git && \
    apt install -y make && \
    apt install -y curl && \
    apt install -y pkg-config && \
    apt install -y build-essential && \
    apt install -y libavformat-dev && \
    apt install -y libavcodec-dev && \
    apt install -y libavdevice-dev && \
    apt install -y libavutil-dev && \
    apt install -y libswscale-dev && \
    apt install -y libswresample-dev && \
    apt install -y libavfilter-dev && \
    apt clean && rm -rf /var/lib/apt/lists/*

# 設置工作目錄
WORKDIR /usr/src/app

# uv 在 bind-mount 下使用固定 venv 路徑，避免被 /usr/src/app 覆蓋
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 先複製 lock 相關檔案（單獨一層，便於 cache）
COPY pyproject.toml uv.lock /usr/src/app/

# 安裝 Python 套件（不執行應用程式）
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --retries 5 --timeout 120 uv

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# 設置預設指令
# CMD ["python", "main.py"]
