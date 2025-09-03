from flask import Flask, jsonify, request, send_file
import os

app = Flask(__name__)
file_dir = r'D:\data\code\xzd_script\others\libreOffice\tmp'  # 替换为实际存储路径

@app.route('/wopi/files/<filename>', methods=['GET'])
def check_file_info(filename):
    path = os.path.join(file_dir, filename)
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    return jsonify({
        "BaseFileName": filename,
        "Size": os.path.getsize(path),
        "OwnerId": "user1",
        "UserId": "user1",
        "UserCanWrite": False,
        "ReadOnly": True
    })

@app.route('/wopi/files/<filename>/contents', methods=['GET'])
def get_file(filename):
    return send_file(os.path.join(file_dir, filename), as_attachment=True)

@app.route('/wopi/files/<filename>/contents', methods=['POST', 'PUT'])
def put_file(filename):
    with open(os.path.join(file_dir, filename), 'wb') as f:
        f.write(request.data)
    return jsonify({"status": "saved"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)