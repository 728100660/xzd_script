FROM python:3.10-slim

# 安装 WeasyPrint 依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libssl-dev \
    libxml2 \
    libxslt1.1 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 拷贝项目文件
COPY . .

# 安装 Python 包
RUN pip install --no-cache-dir -r requirements.txt

# 默认运行测试脚本
CMD ["python", "main.py"]
