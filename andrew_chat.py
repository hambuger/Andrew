import time
import os
import traceback
from config.global_logger import logger
from paddlespeech.cli.asr.infer import ASRExecutor
from openai_util.s_auto_gpt import run_conversation_v2, push_message
from voice_util.kws.audio_kws import get_audio
from voice_util.tts.voice_tts import text_2_audio
from database_util.redis.redis_client import api_key_manager

# 创建ASR执行器
asr = ASRExecutor()

# 记录最后一次检测到有效输入的时间
last_input_time = 0
# 是否激活了语音对话
audio_active = False
# 默认音频文件路径
file_path = 'audio.wav'
# 记录上一次对话回应消息的ID
parent_id = '0'
while True:
    try:
        get_audio(audio_active, file_path, last_input_time)
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
            parent_id = '0'
            text_2_audio("再见")
            if api_key_manager.get_key_value('AUDIO_KEY') == os.getenv('os_name'):
                api_key_manager.delete_key('AUDIO_KEY')
            continue
        push_message({"role": "user", "content": result})
        (answer, msg_Id) = run_conversation_v2(result, parent_id)
        if msg_Id:
            parent_id = msg_Id
        if not answer:
            continue
        push_message({"role": "assistant", "content": answer})
        logger.info(f"AI回复：{answer}")
        text_2_audio(answer)
        last_input_time = time.time()
    except Exception as e:
        logger.error(e)
        # 打印异常堆栈
        logger.error(traceback.format_exc())
        continue
    finally:
        if api_key_manager.get_key_value('AUDIO_KEY') == os.getenv('os_name'):
            api_key_manager.delete_key('AUDIO_KEY')
