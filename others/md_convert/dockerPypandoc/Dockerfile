FROM python:3.10-slim

# 安装 unzip 用于解压 pandoc
RUN apt-get update && apt-get install -y unzip && rm -rf /var/lib/apt/lists/*

# 下载并解压 pandoc 二进制文件（无系统安装）
RUN curl -L -o pandoc.zip https://github.com/jgm/pandoc/releases/download/3.2/pandoc-3.2-1-amd64.deb && \
    dpkg -x pandoc-3.2-1-amd64.deb /usr/local && \
    ln -s /usr/local/usr/bin/pandoc /usr/local/bin/pandoc

# 设置工作目录
WORKDIR /app
COPY . .

# 安装 Python 包
RUN pip install pypandoc markdown

CMD ["python", "main.py"]
