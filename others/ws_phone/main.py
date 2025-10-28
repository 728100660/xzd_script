from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import wave
import os

app = FastAPI()

@app.websocket("/ws/audio")
async def websocket_audio(ws: WebSocket):
    await ws.accept()
    print("WebSocket 连接建立")

    # 用来存放接收到的音频数据
    audio_chunks = []

    try:
        while True:
            data = await ws.receive_bytes()  # 接收二进制数据
            audio_chunks.append(data)

    except WebSocketDisconnect:
        print("WebSocket 连接断开")
        # 保存 WAV 文件
        filename = "recorded.wav"
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(1)          # 单声道
            wf.setsampwidth(2)          # 16 bit
            wf.setframerate(44100)      # 采样率
            wf.writeframes(b"".join(audio_chunks))
        print(f"音频已保存到 {filename}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
