import io
import os
import tempfile
import time

import openai
import speech_recognition as sr
from paddlespeech.cli.asr.infer import ASRExecutor
from dotenv import load_dotenv
from hai_chat.s_auto_gpt import run_conversation_v2
from config.global_logger import logger
from voice_util.voice_tts import file_2_audio

# 加载配置文件
load_dotenv()
# 创建Recognizer和Microphone实例
r = sr.Recognizer()
mic = sr.Microphone()

# 创建ASR执行器
asr = ASRExecutor()

# 0待机 1:对话中
audio_status = 0

# 记录最后一次检测到有效输入的时间
last_input_time = 0

# 如果一段时间内没有检测到有效的输入，就进入待机状态
idle_timeout = 60

while True:
    with mic as source:
        # 循环，以便我们可以连续地进行语音识别
        r.adjust_for_ambient_noise(source)  # 调整麦克风的噪声水平
        audio = r.listen(source, phrase_time_limit=20)  # 开始监听麦克风输入

    # 创建一个临时文件
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    # 将音频数据写入临时文件
    wave_date = audio.get_wav_data()
    temp_file.write(wave_date)
    # 关闭临时文件
    temp_file.close()
    # 获取临时文件的路径
    temp_file_path = temp_file.name
    result = None
    if audio_status == 0:
        # 执行ASR并打印结果
        result = asr(model='conformer_wenetspeech', audio_file=temp_file_path, force_yes=True)
        logger.info(f"识别语音：{result}")
        if not result or not '安德鲁' in result:
            continue
        last_input_time = time.time()
        audio_status = 1
    if not result:
        wav_date = io.BytesIO(wave_date)
        wav_date.name = "SpeechRecognition_audio.wav"
        openai.api_key = os.getenv("WHISPER_MODEL_KEY")
        result = openai.Audio.transcribe("whisper-1", wav_date, language="zh")["text"]
        logger.info(f"识别语音：{result}")
    if not result:
        # 如果一段时间没有检测到有效的输入，就进入待机状态
        if time.time() - last_input_time > idle_timeout:
            logger.info("暂时休眠")
            audio_status = 0
        continue
    if '再见' in result or '再見' in result:
        logger.info("Bye!")
        audio_status = 0
        file_2_audio("再见", True)
        continue
    answer = run_conversation_v2(result)
    if not answer:
        continue
    logger.info(f"AI回复：{answer}")
    file_2_audio(answer, True)
    # 删除临时文件
    last_input_time = time.time()
    os.remove(temp_file_path)
