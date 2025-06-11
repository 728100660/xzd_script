FROM weasyprint/ubuntu:latest

# 设置工作目录
WORKDIR /app

# 复制文件
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY md2pdf.py ./
COPY input.md ./
RUN mkdir -p /output

# 默认运行转换脚本
CMD ["python3", "md2pdf.py"]
