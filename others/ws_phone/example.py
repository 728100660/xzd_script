import asyncio
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from funasr import AutoModel
import base64
import json
import uvicorn
import time
import webrtcvad

# 初始化 VAD（0-3，越高越敏感）
vad = webrtcvad.Vad(2)

app = FastAPI()

# === 初始化模型 ===
# VAD模型
vad_model = AutoModel(model="fsmn-vad", model_revision="v2.0.4")
print("✅ FSMN-VAD 模型加载完成")

# ASR模型
chunk_size = [0, 10, 5]
encoder_chunk_look_back = 4
decoder_chunk_look_back = 1
asr_model = AutoModel(model="paraformer-zh-streaming")
print("✅ Paraformer ASR 模型加载完成")

# 存储每个会话的上下文缓存
session_cache = {}


class SessionStateManager:
    """管理会话状态"""

    def __init__(self, sample_rate=8000):
        self.sample_rate = sample_rate
        self.vad_cache = {}
        self.asr_cache = {}

        # 音频缓冲区
        self.vad_buffer = np.array([], dtype=np.float32)  # 用于VAD检测
        self.asr_buffer = np.array([], dtype=np.float32)  # 用于ASR识别

        # 状态管理
        self.is_speaking = False
        self.silence_count = 0
        self.silence_threshold = 10  # 连续静音次数阈值

        # VAD参数
        self.vad_chunk_size = 200  # ms
        self.vad_chunk_stride = int(self.vad_chunk_size * self.sample_rate / 1000)

        # ASR参数
        self.asr_chunk_stride = chunk_size[1] * 960  # 600ms


@app.websocket("/ws/asr/{session_id}")
async def ws_asr(websocket: WebSocket, session_id: str):
    await websocket.accept()
    print(f"🎧 新会话: {session_id}")

    # 初始化会话状态管理器
    session_manager = SessionStateManager()
    session_cache[session_id] = session_manager

    try:
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=0.5)
            except asyncio.TimeoutError:
                # 超时处理：如果在说话状态但长时间没有新数据，结束当前语音
                if session_manager.is_speaking:
                    session_manager.silence_count += 1
                    if session_manager.silence_count >= session_manager.silence_threshold:
                        await _finalize_speech(session_id, websocket)
                continue

            msg = json.loads(message)

            if msg["type"] == "audio":
                await _process_audio_chunk(session_id, websocket, msg["data"])
            elif msg["type"] == "end":
                await _finalize_session(session_id, websocket)
                break

    except WebSocketDisconnect:
        print(f"❌ 连接断开: {session_id}")
    except Exception as e:
        print(f"❌ 处理错误 {session_id}: {e}")
        await websocket.send_text(json.dumps({"type": "error", "data": str(e)}))
    finally:
        session_cache.pop(session_id, None)


def rms_energy(buf: np.ndarray):
    import math
    # buf 已经是 float32（-1..1），计算 RMS 能量
    if len(buf) == 0:
        return 0.0
    return math.sqrt(np.mean(buf.astype(np.float64) ** 2))


async def _process_audio_chunk(session_id, websocket, audio_data):
    """处理音频数据块"""
    session_manager = session_cache[session_id]

    # 解码音频
    audio_bytes = base64.b64decode(audio_data)
    audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
    audio_chunk = audio_int16.astype(np.float32) / 32768.0

    # 同时累积到VAD和ASR缓冲区
    session_manager.vad_buffer = np.concatenate([session_manager.vad_buffer, audio_chunk])
    session_manager.asr_buffer = np.concatenate([session_manager.asr_buffer, audio_chunk])

    frame_duration = 30  # ms   # TODO 之后作为session_manager里面的参数定义
    frame_length = int(session_manager.sample_rate * frame_duration / 1000)  # e.g. 240 samples for 8kHz

    # ===== 使用 WebRTC VAD 检测语音段 =====
    while len(session_manager.vad_buffer) >= frame_length:
        frame = session_manager.vad_buffer[:frame_length]
        session_manager.vad_buffer = session_manager.vad_buffer[frame_length:]

        # 转回 bytes 供 VAD 判断
        frame_bytes = (frame * 32768).astype(np.int16).tobytes()
        is_speech = vad.is_speech(frame_bytes, session_manager.sample_rate)

        if is_speech:
            if not session_manager.is_speaking:
                print("🎤 WebRTC VAD: 检测到语音开始")
                session_manager.is_speaking = True
            session_manager.silence_count = 0
        else:
            if session_manager.is_speaking:
                session_manager.silence_count += 1
                # 连续静音超过 600ms 就认为说完
                if session_manager.silence_count * frame_duration >= 600:
                    print("🔇 WebRTC VAD: 检测到语音结束")
                    await _finalize_speech(session_id, websocket)

    # === ASR 识别 (仅在检测到语音时进行) ===
    if session_manager.is_speaking:
        while len(session_manager.asr_buffer) >= session_manager.asr_chunk_stride:
            asr_chunk = session_manager.asr_buffer[:session_manager.asr_chunk_stride]
            session_manager.asr_buffer = session_manager.asr_buffer[session_manager.asr_chunk_stride:]

            try:
                # ASR识别
                asr_res = asr_model.generate(
                    input=asr_chunk,
                    cache=session_manager.asr_cache,
                    is_final=False,
                    chunk_size=chunk_size,
                    encoder_chunk_look_back=encoder_chunk_look_back,
                    decoder_chunk_look_back=decoder_chunk_look_back,
                )

                text = _extract_text_from_result(asr_res)
                if text and text.strip():
                    print(f"🗣️ 实时识别: {text}")
                    await websocket.send_text(json.dumps({
                        "type": "interim_text",
                        "data": text.strip()
                    }))

            except Exception as e:
                print(f"ASR处理错误: {e}")


async def _finalize_speech(session_id, websocket):
    """处理语音结束"""
    session_manager = session_cache[session_id]

    if not session_manager.is_speaking:
        return

    print("🔄 处理语音结束...")

    # 处理ASR缓冲区中剩余的音频
    if len(session_manager.asr_buffer) > 0:
        try:
            asr_res_final = asr_model.generate(
                input=session_manager.asr_buffer,
                cache=session_manager.asr_cache,
                is_final=True,
                chunk_size=chunk_size,
                encoder_chunk_look_back=encoder_chunk_look_back,
                decoder_chunk_look_back=decoder_chunk_look_back,
            )

            text = _extract_text_from_result(asr_res_final)
            if text and text.strip():
                print(f"📝 最终识别: {text}")
                await websocket.send_text(json.dumps({
                    "type": "final_text",
                    "data": text.strip()
                }))

        except Exception as e:
            print(f"最终ASR处理错误: {e}")

    # 重置状态
    session_manager.is_speaking = False
    session_manager.silence_count = 0
    session_manager.asr_buffer = np.array([], dtype=np.float32)

    # 重置VAD缓存，开始新的检测
    session_manager.vad_cache = {}


async def _finalize_session(session_id, websocket):
    """结束整个会话"""
    session_manager = session_cache[session_id]

    # 如果还在说话状态，先结束当前语音
    if session_manager.is_speaking:
        await _finalize_speech(session_id, websocket)

    await websocket.send_text(json.dumps({"type": "done"}))
    print(f"✅ 会话完成: {session_id}")


def _extract_text_from_result(res):
    """从ASR结果中提取文本"""
    if not res:
        return ""

    if isinstance(res, list) and len(res) > 0:
        if isinstance(res[0], dict):
            return res[0].get("text", "")
        else:
            return str(res[0])
    elif isinstance(res, dict):
        return res.get("text", "")
    else:
        return str(res)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )