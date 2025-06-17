import debugpy
debugpy.listen(("0.0.0.0", 5678))
print("Debugger is listening on port 5678")
debugpy.wait_for_client()

from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello from Dev Container!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
