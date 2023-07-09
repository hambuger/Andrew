import time

import speech_recognition as sr
from dotenv import load_dotenv
from paddlespeech.cli.asr.infer import ASRExecutor

from config.global_logger import logger
from hai_chat.s_auto_gpt import run_conversation_v2
from voice_util.kws.audio_kws import get_audio
from voice_util.tts.voice_tts import text_2_audio

# 加载配置文件
load_dotenv()
# 创建Recognizer和Microphone实例
r = sr.Recognizer()
mic = sr.Microphone()

# 创建ASR执行器
asr = ASRExecutor()

# 记录最后一次检测到有效输入的时间
last_input_time = 0

audio_active = False
file_path = 'audio.wav'
while True:
    audio_active = get_audio(audio_active, file_path, last_input_time)
    result = None
    # 执行ASR并打印结果
    result = asr(model='conformer_wenetspeech', audio_file=file_path, force_yes=True)
    logger.info(f"识别语音：{result}")
    last_input_time = time.time()
    audio_active = True
    if not result:
        continue
    if '再见' in result or '再見' in result:
        logger.info("Bye!")
        audio_active = False
        text_2_audio("再见")
        continue
    answer = run_conversation_v2(result)
    if not answer:
        continue
    logger.info(f"AI回复：{answer}")
    text_2_audio(answer)
    last_input_time = time.time()
