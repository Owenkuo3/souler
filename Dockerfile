# 使用官方 Python 映像檔
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴套件（包含 swisseph 需要的）
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    libz-dev \
    wget \
    unzip \
    libfreetype6-dev \
    libxft-dev \
    libpng-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*


COPY . /app

# 安裝 Python 套件
RUN pip install --upgrade pip && pip install -r requirements.txt

ENV DJANGO_SETTINGS_MODULE=astro_project.settings

WORKDIR /app/astro_project

RUN python manage.py collectstatic --noinput

