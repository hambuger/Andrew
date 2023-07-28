import time
import os
import traceback
from config.global_logger import logger
from voice_util.asr.asr_invoke import audio_to_text
from openai_util.s_auto_gpt import run_conversation_v2, push_message
from voice_util.kws.audio_kws import get_audio, set_user_input_str
from voice_util.tts.voice_tts import text_2_audio, stop_speak
from database_util.redis.redis_client import api_key_manager
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(10)
input_str = None

# 记录最后一次检测到有效输入的时间
last_input_time = 0
# 是否激活了语音对话
audio_active = False
# 默认音频文件路径
file_path = 'tmp/audio.wav'
# 记录上一次对话回应消息的ID
parent_id = '0'


def get_input():
    global input_str
    while True:
        input_str = input()
        set_user_input_str(input_str)
        if not input_str:
            continue
        if input_str.lower() == 'stop':
            stop_speak()
            input_str = None
            continue


executor.submit(get_input)
logger.info("语音对话已启动")
print("语音对话已启动")
while True:
    try:
        audio_text = None
        if get_audio(audio_active, file_path, last_input_time):
            # 执行ASR并打印结果
            audio_text = audio_to_text(file_path)
            logger.debug(f"识别语音：{audio_text}")
            last_input_time = time.time()
            audio_active = True
        if not audio_text and not input_str:
            continue
        if audio_text and '再见' in audio_text:
            logger.debug("再见")
            audio_active = False
            parent_id = '0'
            text_2_audio("再见")
            print('\033[32m' + "再见" + '\033[0m')
            if api_key_manager.get_key_value('AUDIO_KEY') == os.getenv('OS_NAME'):
                api_key_manager.delete_key('AUDIO_KEY')
            continue
        audio_text = (f"""{input_str}\n{audio_text}""" if audio_text else input_str) if input_str else audio_text
        if audio_text != input_str:
            print('\033[32m' + f"{os.getenv('MY_NAME')}：{audio_text}" + '\033[0m')
        push_message({"role": "user", "content": audio_text})
        (answer, msg_Id) = run_conversation_v2(audio_text, parent_id)
        if msg_Id:
            parent_id = msg_Id
        if not answer:
            continue
        push_message({"role": "assistant", "content": answer})
        logger.debug(f"AI回复：{answer}")
        print('\033[31m' + f"AI回复：{answer}" + '\033[0m')
        text_2_audio(answer)
        last_input_time = time.time()
    except Exception as e:
        logger.error(e)
        # 打印异常堆栈
        logger.error(traceback.format_exc())
        continue
    finally:
        if api_key_manager.get_key_value('AUDIO_KEY') == os.getenv('OS_NAME'):
            api_key_manager.delete_key('AUDIO_KEY')
