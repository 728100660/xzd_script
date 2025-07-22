from flask import Flask, jsonify, request
import mcp_manager

app = Flask(__name__)


@app.route('/start_all', methods=['GET'])
def start_all():
    mcp_manager.start_all()
    return jsonify({"status": "started"})


@app.route('/stop/<name>', methods=['GET'])
def stop(name):
    mcp_manager.stop_tool(name)
    return jsonify({"status": f"{name} stopped"})


@app.route('/status', methods=['GET'])
def status():
    return jsonify(mcp_manager.get_status())


@app.route("/start_all2", methods=["GET"])
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
    return mcp_manager.invoke("amap-maps", mcp_request)


@app.route("/", methods=["GET"])
def index():
    return {"status": "MCP wrapper runni2ng"}, 200


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5001)
