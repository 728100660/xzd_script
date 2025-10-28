# web socket实时通话
# pip install fastapi uvicorn
import asyncio
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from funasr import AutoModel
import base64
import json
import uvicorn
import torch
from silero_vad import load_silero_vad, VADIterator
import time

app = FastAPI()

# === 初始化 FunASR 流式模型 ===
chunk_size = [0, 10, 5]
encoder_chunk_look_back = 4
decoder_chunk_look_back = 1

model = AutoModel(model="paraformer-zh-streaming")
print("✅ FunASR 模型加载完成")

# === 初始化 Silero VAD ===
# 尝试加载模型，如果失败则提示安装
try:
    torch_model, utils = load_silero_vad()
    get_speech_timestamps = utils[0]
    print("✅ Silero VAD 模型加载完成")
except Exception as e:
    print(f"❌ Silero VAD 加载失败，请确保已安装: pip install silero-vad\n错误信息: {e}")
    # 这里可以选择退出或降级到其他VAD方案
    raise

# 存储每个会话的上下文缓存
session_cache = {}


class SessionVADManager:
    """管理会话的VAD状态"""

    def __init__(self, sampling_rate=16000):
        self.vad_iterator = VADIterator(
            model=torch_model,
            threshold=0.5,  # 语音概率阈值，可根据环境调整[citation:10]
            sampling_rate=sampling_rate,
            min_silence_duration_ms=100,  # 最小静音时长[citation:10]
            speech_pad_ms=30  # 语音片段前后填充[citation:10]
        )
        self.sampling_rate = sampling_rate
        self.is_speaking = False
        self.last_voice_time = 0
        self.speech_timeout = 1.5  # 语音结束超时（秒）

    def process_audio(self, audio_chunk):
        """处理音频块，返回VAD状态"""
        current_time = time.time()

        # 使用VADIterator处理音频块[citation:6]
        speech_dict = self.vad_iterator(audio_chunk, return_seconds=False)

        if speech_dict is not None:
            self.is_speaking = True
            self.last_voice_time = current_time
            return "speaking"
        else:
            # 检查是否超时
            if self.is_speaking and (current_time - self.last_voice_time) > self.speech_timeout:
                self.is_speaking = False
                return "speech_end"
            elif not self.is_speaking:
                return "silence"
            else:
                return "speaking"  # 仍在说话，未超时

    def reset(self):
        """重置VAD状态"""
        self.vad_iterator.reset_states()
        self.is_speaking = False
        self.last_voice_time = 0


class SentenceAccumulator:
    """智能句子累积器"""

    def __init__(self):
        self.current_sentence = ""
        self.last_add_time = 0
        self.sentence_timeout = 1.2  # 句子完成超时
        self.min_sentence_length = 3  # 最小句子长度

    def add_text(self, new_text, is_final=False):
        """添加文本并判断是否形成完整句子"""
        if not new_text.strip():
            return None, False

        current_time = time.time()
        merged_text = self._merge_text(self.current_sentence, new_text)

        # 更新当前句子
        self.current_sentence = merged_text
        self.last_add_time = current_time

        # 判断句子结束的条件
        sentence_end = False
        send_text = None

        # 条件1: 强制结束（如VAD检测到语音结束）
        if is_final:
            send_text = self.current_sentence
            self.current_sentence = ""
            sentence_end = True

        # 条件2: 检测到自然句子结束（句号、问号等）
        elif self._has_sentence_end(merged_text):
            send_text = self.current_sentence
            self.current_sentence = ""
            sentence_end = True

        # 条件3: 超时且有一定长度
        elif (current_time - self.last_add_time > self.sentence_timeout and
              len(merged_text) >= self.min_sentence_length):
            send_text = self.current_sentence
            self.current_sentence = ""
            sentence_end = True

        return send_text, sentence_end

    def _merge_text(self, old_text, new_text):
        """智能合并文本，去除重叠部分"""
        if not old_text:
            return new_text

        # 简单重叠检测：检查新文本开头是否与旧文本结尾重复
        overlap_len = min(len(old_text), len(new_text), 6)  # 检查最多6个字符
        for i in range(overlap_len, 0, -1):
            if old_text.endswith(new_text[:i]):
                return old_text + new_text[i:]

        return old_text + new_text

    def _has_sentence_end(self, text):
        """检查文本是否包含句子结束标志"""
        end_marks = ['。', '？', '！', '.', '?', '!', '，', ',']
        return any(text.endswith(mark) for mark in end_marks)

    def get_current_text(self):
        """获取当前累积的文本"""
        return self.current_sentence

    def reset(self):
        """重置累积器"""
        self.current_sentence = ""
        self.last_add_time = 0


@app.websocket("/ws/asr/{session_id}")
async def ws_asr(websocket: WebSocket, session_id: str):
    await websocket.accept()
    print(f"🎧 新会话: {session_id}")

    # 初始化会话组件
    vad_manager = SessionVADManager(sampling_rate=16000)
    sentence_accumulator = SentenceAccumulator()

    session_cache[session_id] = {
        "cache": {},
        "buffer": np.array([], dtype=np.float32),
        "vad_manager": vad_manager,
        "sentence_accumulator": sentence_accumulator,
        "last_audio_time": time.time()
    }

    try:
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=0.3)
            except asyncio.TimeoutError:
                # 检查VAD超时
                session_data = session_cache[session_id]
                vad_manager = session_data["vad_manager"]

                # 处理VAD超时
                vad_result = vad_manager.process_audio(None)  # 传入None来检查超时
                if vad_result == "speech_end":
                    await _finalize_current_utterance(session_id, websocket)
                continue

            msg = json.loads(message)
            session_data = session_cache[session_id]
            session_data["last_audio_time"] = time.time()

            if msg["type"] == "audio":
                await _process_audio_data(session_id, websocket, msg["data"])

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


async def _process_audio_data(session_id, websocket, audio_data):
    """处理音频数据"""
    session_data = session_cache[session_id]

    # 解码音频
    audio_bytes = base64.b64decode(audio_data)
    audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
    chunk = audio_int16.astype(np.float32) / 32768.0

    # 使用Silero VAD处理[citation:6]
    vad_manager = session_data["vad_manager"]
    vad_result = vad_manager.process_audio(audio_int16)  # 使用int16格式的音频

    # 累积音频缓存
    buf = session_data["buffer"]
    buf = np.concatenate([buf, chunk])
    chunk_stride = chunk_size[1] * 960

    # 处理累积的音频块
    processed_count = 0
    while len(buf) >= chunk_stride and processed_count < 2:
        speech_chunk = buf[:chunk_stride]
        buf = buf[chunk_stride:]
        processed_count += 1

        # ASR识别
        text = await _run_asr(session_id, speech_chunk, is_final=False)

        if text:
            # 发送实时文本
            await websocket.send_text(json.dumps({
                "type": "interim_text",
                "data": text
            }))

            # 累积到句子中
            sentence_accumulator = session_data["sentence_accumulator"]
            complete_sentence, is_end = sentence_accumulator.add_text(text)

            if complete_sentence and is_end:
                print(f"📝 完整句子: {complete_sentence}")
                await websocket.send_text(json.dumps({
                    "type": "sentence",
                    "data": complete_sentence
                }))

                # 这里可以添加发送给LLM的逻辑
                await _send_to_llm(websocket, complete_sentence)

    session_data["buffer"] = buf

    # 如果VAD检测到语音结束，处理当前话语
    if vad_result == "speech_end":
        await _finalize_current_utterance(session_id, websocket)


async def _finalize_current_utterance(session_id, websocket):
    """结束当前话语"""
    session_data = session_cache[session_id]

    # 处理剩余音频
    buf = session_data["buffer"]
    if len(buf) > 0:
        text = await _run_asr(session_id, buf, is_final=True)

        if text:
            await websocket.send_text(json.dumps({
                "type": "final_text",
                "data": text
            }))

            # 强制完成当前句子
            sentence_accumulator = session_data["sentence_accumulator"]
            complete_sentence, _ = sentence_accumulator.add_text(text, is_final=True)

            if not complete_sentence:
                # 如果没有检测到完整句子，但当前有累积文本，也发送
                current_text = sentence_accumulator.get_current_text()
                if current_text:
                    complete_sentence = current_text
                    sentence_accumulator.reset()

            if complete_sentence:
                print(f"🚀 发送给LLM: {complete_sentence}")
                await websocket.send_text(json.dumps({
                    "type": "llm_ready",
                    "data": complete_sentence
                }))

    # 重置状态
    session_data["buffer"] = np.array([], dtype=np.float32)
    session_data["vad_manager"].reset()


async def _run_asr(session_id, audio_chunk, is_final=False):
    """运行ASR识别"""
    session_data = session_cache[session_id]
    cache = session_data["cache"]

    try:
        res = model.generate(
            input=audio_chunk,
            cache=cache,
            is_final=is_final,
            chunk_size=chunk_size,
            encoder_chunk_look_back=encoder_chunk_look_back,
            decoder_chunk_look_back=decoder_chunk_look_back,
        )

        # 更新缓存
        if isinstance(res, dict) and "cache" in res:
            session_data["cache"] = res["cache"]

        # 提取文本
        if isinstance(res, list) and len(res) > 0:
            text = res[0].get("text", "")
        elif isinstance(res, dict):
            text = res.get("text", "")
        else:
            text = ""

        return text.strip()

    except Exception as e:
        print(f"ASR识别错误: {e}")
        return ""


async def _send_to_llm(websocket, text):
    """发送文本给LLM（这里需要你实现LLM集成）"""
    # 这里是发送给LLM的入口点
    # 你可以在这里调用你的LLM模型
    pass


async def _finalize_session(session_id, websocket):
    """结束会话"""
    await _finalize_current_utterance(session_id, websocket)
    await websocket.send_text(json.dumps({"type": "done"}))
    print(f"✅ 会话完成: {session_id}")


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )