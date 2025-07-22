import subprocess
import json
from flask import Flask, request, jsonify
import threading

app = Flask(__name__)

# 启动 MCP 工具进程（只启动一次）
proc = subprocess.Popen(
    ["npx.cmd", "-y", "@amap/amap-maps-mcp-server"],  # Windows 用 npx.cmd
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    shell=True,
    text=True,
    bufsize=1,
)

lock = threading.Lock()  # 避免并发写入 stdin/stdout

@app.route("/invoke", methods=["GET"])
def invoke():
    # input_data = request.get_json()

    # 构造 MCP ToolInvokeRequest
    mcp_request = {
        "type": "tool-invoke-request",
        "tool_name": "amap-maps",
        "tool_input": {
            "location": "深圳"
        }
    }

    with lock:
        try:
            # 发送请求
            proc.stdin.write(json.dumps(mcp_request) + "\n")
            proc.stdin.flush()

            # 读取响应（逐行读取直到 tool-invoke-response）
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                try:
                    msg = json.loads(line)
                    if msg.get("type") == "tool-invoke-response":
                        return jsonify(msg)
                except json.JSONDecodeError:
                    continue

        except Exception as e:
            return jsonify({"error": str(e)}), 500


@app.route("/")
def index():
    return {"status": "MCP wrapper running"}, 200


if __name__ == '__main__':
    app.run(port=3333)
