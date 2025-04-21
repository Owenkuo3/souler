# 使用 Python 官方映像檔作為基底
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 複製專案檔案（目前還沒檔案，但後面會有）
COPY . .

# 安裝 Django（你可以換成 requirements.txt 後再調整）
RUN pip install django

# 預設啟動指令（之後會修改）
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
