import json
import os
import subprocess
import threading
import time
from pathlib import Path
from flask import jsonify

CONFIG_PATH = './mcp.config.json'
LOG_DIR = Path('./logs')
LOG_DIR.mkdir(exist_ok=True)

CHECK_INTERVAL = 5  # 秒
mcp_processes = {}
mcp_threads = {}
shutdown_flags = {}


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f).get("mcpServers", {})


def start_tool(name, server_config):
    command = server_config.get("command")
    args = server_config.get("args", [])
    env_vars = server_config.get("env", {})
    from shutil import which

    npx_path = which(command)
    full_cmd = [npx_path] + args
    env = os.environ.copy()
    env.update(env_vars)

    stdout_log = open(LOG_DIR / f'{name}.out.log', 'a')
    stderr_log = open(LOG_DIR / f'{name}.err.log', 'a')
    stdout = subprocess.PIPE
    stderr = subprocess.PIPE
    stdin = subprocess.PIPE

    proc = subprocess.Popen(
        full_cmd,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        env=env,
        universal_newlines=True
    )

    mcp_processes[name] = {
        "proc": proc,
        "stdout": stdout_log,
        "stderr": stderr_log
    }
    shutdown_flags[name] = False
    print(f"✅ MCP工具 {name} 启动成功，PID={proc.pid}")


def watchdog(name, server_config):
    while not shutdown_flags.get(name, False):
        proc_info = mcp_processes.get(name)
        proc = proc_info['proc'] if proc_info else None
        if proc and proc.poll() is not None:
            print(f"⚠️ {name} 异常退出，自动重启中...")
            start_tool(name, server_config)
        time.sleep(CHECK_INTERVAL)


def start_all():
    servers = load_config()
    for name, cfg in servers.items():
        start_tool(name, cfg)
        t = threading.Thread(target=watchdog, args=(name, cfg), daemon=True)
        t.start()
        mcp_threads[name] = t


def stop_tool(name):
    if name in mcp_processes:
        shutdown_flags[name] = True
        proc_info = mcp_processes.pop(name)
        proc_info['proc'].terminate()
        proc_info['stdout'].close()
        proc_info['stderr'].close()
        print(f"🛑 MCP工具 {name} 已停止")


def get_status():
    status = {}
    for name, info in mcp_processes.items():
        proc = info['proc']
        status[name] = {
            "pid": proc.pid,
            "running": proc.poll() is None
        }
    return status

def invoke(name, mcp_request):
    proc = mcp_processes.get(name, {}).get("proc")

    # 连续读几行，看有没有 tool-description
    for _ in range(10):
        line = proc.stdout.readline()
        print("接收到行:", line.strip())
        try:
            msg = json.loads(line)
            if msg.get("type") == "tool-description":
                print("✅ 工具描述:",
                      json.dumps(msg, indent=2, ensure_ascii=False))
                break
        except Exception as e:
            print("忽略非 JSON 行")
        time.sleep(1)
    try:
        # 发送请求
        proc.stdin.write(json.dumps(mcp_request) + "\n")
        proc.stdin.flush()

        # 读取响应（逐行读取直到 tool-invoke-response）
        while True:
            time.sleep(1)
            line = proc.stdout.readline()
            print(f"读取数据：{line}")
            if not line:
                continue
            try:
                msg = json.loads(line)
                if msg.get("type") == "tool-invoke-response":
                    return jsonify(msg)
            except json.JSONDecodeError:
                continue

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return 1


if __name__ == '__main__':
    start_all()
    stop_tool("amap-maps")