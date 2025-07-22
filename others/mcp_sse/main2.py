import subprocess
import json
import time

from shutil import which
command = which('npx')
npx_path = which(command)


env = {
    "AMAP_MAPS_API_KEY": "fb8ee395d6001e33dd33f360588d0b99"
}
proc = subprocess.Popen(
    [npx_path, '-y', '@amap/amap-maps-mcp-server'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env=env,
    text=True
)

# 连续读几行，看有没有 tool-description
for _ in range(10):
    line = proc.stdout.readline()
    print("接收到行:", line.strip())
    try:
        msg = json.loads(line)
        if msg.get("type") == "tool-description":
            print("✅ 工具描述:", json.dumps(msg, indent=2, ensure_ascii=False))
            break
    except Exception as e:
        print("忽略非 JSON 行")
    time.sleep(1)
