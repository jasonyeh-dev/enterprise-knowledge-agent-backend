# 1. 使用官方極輕量版的 Python 3.11 基礎映像檔 (瘦身思維)，已包含OS
FROM python:3.11-slim

# 2. 設定容器內的工作目錄
WORKDIR /app

# 3. 解決 Python 列印日誌可能卡住的問題
ENV PYTHONUNBUFFERED=1

# 4. 先複製 requirements.txt，利用 Docker 快取機制加速未來建置
COPY requirements.txt .

# 5. 安裝套件 (不保留快取，讓 Image 更小)
RUN pip install --no-cache-dir -r requirements.txt

# 6. 把專案內的所有程式碼複製到容器內
COPY . .

# 7. 暴露 8080 Port (這是 GCP Cloud Run 的預設 Port)
EXPOSE 8080

# 8. 啟動 FastAPI 伺服器
# 💡 注意：一定要綁定 0.0.0.0，不然外部網路進不來
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080","--forwarded-allow-ips", "*" ,"--proxy-headers"]