# 選擇基礎映像
FROM python:3.10-slim

# 安裝必要的程式
RUN apt update && \
    apt install -y ffmpeg && \
    apt install -y git && \
    apt install -y make && \
    apt install -y curl && \
    apt clean && rm -rf /var/lib/apt/lists/*

# 設置工作目錄
WORKDIR /usr/src/app

# 將依賴需求檔案複製到容器中（如果有需要）
# COPY requirements.txt .
# RUN pip install -r requirements.txt

# 設置預設指令（如果需要）
# CMD ["python", "main.py"]