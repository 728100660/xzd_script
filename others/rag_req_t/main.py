
import requests
import os

url = "http://192.168.17.241:5000/parse_pdf/"


file_path = r"D:\data\code\xzd_script\others\rag_req_t\测试图像流式传输的fix_精简版 - QA.pdf"
file_name = os.path.basename(file_path)
files = {
    'file': (file_name, open(file_path, 'rb'), 'application/pdf')
}

data = {
    'method': 'simple',
    'model': 'qwen2.5-omni-7b',
    'verbose': 'true'
}

response = requests.post(url, files=files, data=data)

with open('document.zip', 'wb') as f:
    f.write(response.content)
