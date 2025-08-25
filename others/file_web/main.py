# pip install flask
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# 上传文件保存目录
UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"code": 400, "msg": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"code": 400, "msg": "No selected file"}), 400

    # 保存文件到 uploads 目录
    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    # 模拟一个文件访问 URL（实际可改成你服务器的 URL）
    file_url = f"http://127.0.0.1:5000/files/{file.filename}"

    # 返回响应
    return jsonify({
        "code": 200,
        "msg": "Upload success",
        "file_url": file_url
    })


@app.route("/files/<filename>", methods=["GET"])
def get_file(filename):
    """ 提供已上传文件的访问接口 """
    return jsonify({
        "msg": f"You can access file: {filename}",
        "url": f"http://127.0.0.1:5000/files/{filename}"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
