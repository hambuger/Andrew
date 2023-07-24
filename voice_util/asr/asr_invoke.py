import os

from voice_util.asr.baidu_asr import ApiAsr
from voice_util.asr.baidu_online_asr import OnlineAsr
from voice_util.asr.whisper_asr import WhisperAsr

asr_model = os.getenv('ASR_MODEL', 'BAIDU')


def audio_to_text(audio_file):
    if asr_model == 'BAIDU':
        return ApiAsr().asr_voice(audio_file)
    elif asr_model == 'WHISPER':
        return WhisperAsr().asr_voice(audio_file)
    elif asr_model == 'BAIDU_ONLINE':
        return OnlineAsr().asr_voice(audio_file)
    else:
        return None
