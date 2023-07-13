import collections
import os
import time
import wave
from scipy.signal import resample
import numpy as np
import pvporcupine
import pyaudio
import webrtcvad
from database_util.redis.redis_client import api_key_manager

# 设置一些参数
FORMAT = pyaudio.paInt16
CHANNELS = 1
CHUNK_DURATION_MS = 30  # 每个音频块的毫秒数
PADDING_DURATION_MS = 1000  # 静默持续时间，以毫秒为单位

NUM_PADDING_CHUNKS = int(PADDING_DURATION_MS / CHUNK_DURATION_MS)
# 0 是最不敏感（即最少报告语音活动），3 是最敏感（即最多报告语音活动）
vad = webrtcvad.Vad(0)

pa = pyaudio.PyAudio()
RATE = int(pa.get_default_input_device_info()["defaultSampleRate"]) or 16000
CHUNK_SIZE = int(RATE * CHUNK_DURATION_MS / 1000)
stream = pa.open(format=FORMAT,
                 channels=CHANNELS,
                 rate=RATE,
                 input=True,
                 start=True,
                 frames_per_buffer=CHUNK_SIZE)

# 这个key不是用来接口调用的，而是用来一次性验证身份的
picovoice_access_key = 'oH7xQFgfFONcVY2ll3a7p07sxBBvZqd6dy116lzeig4a2UGmE0+EtQ=='
model_dir = os.getenv('KWS_MODEL_DIR', os.getcwd())

porcupine = pvporcupine.create(
    access_key=picovoice_access_key,
    keyword_paths=[os.path.join(model_dir, '安德鲁_zh_' + os.getenv('os_name') + '_v2_2_0.ppn')],
    model_path=os.path.join(model_dir, 'porcupine_params_zh.pv'),
)
# 是否一次语音结束
got_a_sentence = False

# 唤醒监听的窗口大小
ring_buffer = collections.deque(maxlen=NUM_PADDING_CHUNKS)
# 是否有监听到语音
triggered = False
# 保存音频帧的缓冲区
voiced_frames = []
# 是否检测到关键词
keyword_detected = False
# 记录最后一次检测到有效输入的时间
last_input_time = 0
# 如果一段时间内没有检测到有效的输入，就进入待机状态
idle_timeout = 30


def get_audio(audio_active=False, file_path='audio.wav', last_time=0):
    global triggered, got_a_sentence, voiced_frames, ring_buffer, keyword_detected, last_input_time, idle_timeout
    if last_time != 0:
        last_input_time = last_time
    while True:
        chunk = stream.read(CHUNK_SIZE, exception_on_overflow=False)
        active = vad.is_speech(chunk, RATE)
        ring_buffer.append((chunk, active))
        # print("active: ", active)
        if not triggered:
            num_voiced = len([chunk for chunk, active in ring_buffer if active])
            # print("1 num_voiced: ", num_voiced)
            # print("1 len(ring_buffer): ", len(ring_buffer))
            if num_voiced > 0.5 * len(ring_buffer):
                print('Triggered')
                triggered = True
                voiced_frames.extend([chunk for chunk, _ in ring_buffer])
                ring_buffer.clear()
                last_input_time = time.time()

        else:
            voiced_frames.append(chunk)

            num_unvoiced = len([chunk for chunk, active in ring_buffer if not active])
            # print("2 num_unvoiced: ", num_unvoiced)
            # print("2 len(ring_buffer): ", len(ring_buffer))
            if num_unvoiced > 0.9 * len(ring_buffer):  # 减小这个值
                print('Voice end detected')
                got_a_sentence = True
                triggered = False
                ring_buffer.clear()
        # 如果一段时间没有检测到有效的输入，就进入待机状态
        if time.time() - last_input_time > idle_timeout:
            audio_active = False
            keyword_detected = False
            if api_key_manager.get_key_value('AUDIO_KEY') == os.getenv('os_name'):
                api_key_manager.delete_key('AUDIO_KEY')
        if got_a_sentence:
            print('Processing sentence')
            data = b''.join(voiced_frames)
            if not audio_active:
                # 将数据转换为16位PCM样本的numpy数组
                pcm_data = np.frombuffer(data, dtype=np.int16)
                if RATE != 16000:
                    # 重采样为 16kHz
                    original_duration = len(pcm_data) / RATE
                    pcm_data = resample(pcm_data, num=int(original_duration * 16000))
                # 遍历所有的块，并处理每个块
                for i in range(0, len(pcm_data), porcupine.frame_length):
                    pcm_chunk = pcm_data[i:i + porcupine.frame_length]
                    # 确保块的长度是正确的
                    if len(pcm_chunk) == porcupine.frame_length:
                        pcm_chunk = pcm_chunk.astype(np.int16)
                        result = porcupine.process(pcm_chunk)
                        if result >= 0:
                            keyword_detected = True
                            print("Keyword Detected!")
                            break
            got_a_sentence = False
            voiced_frames = []
            # 如果检测到关键词，保存文件
            if audio_active or keyword_detected:
                print("Wake up!")
                keyword_detected = False
                if not api_key_manager.get_key_value('AUDIO_KEY'):
                    # 没有人在使用，尝试获取锁
                    if api_key_manager.set_nx_key('AUDIO_KEY', os.getenv('os_name'), 60 * 1000):
                        # 获取到锁，可以使用
                        print("Device acquired the lock.")
                    else:
                        # 没有获取到锁，有人在使用
                        print("Device did not acquire the lock. Another device is responding.")
                        break
                elif api_key_manager.get_key_value('AUDIO_KEY') != os.getenv('os_name'):
                    # 有人在使用，不要打扰
                    print("Device did not acquire the lock. Another device is responding.")
                # write to a wav file
                wf = wave.open(file_path, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(pa.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(data)
                wf.close()
                break
