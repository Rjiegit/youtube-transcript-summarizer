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

# 先複製 requirements.txt（單獨一層，便於 cache）
COPY ../requirements.txt /usr/src/app/requirements.txt

# 安裝 Python 套件（不執行應用程式）
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 設置預設指令
# CMD ["python", "main.py"]
