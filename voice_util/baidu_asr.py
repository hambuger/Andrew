from voice_util.voice_asr import VoiceAsr
from paddlespeech.cli.asr.infer import ASRExecutor

asr = ASRExecutor()


class ApiAsr(VoiceAsr):
    # 创建ASR执行器

    def asr_voice(self, voice_file, language='zh'):
        return asr(audio_file=voice_file, force_yes=True)


# print(ApiAsr().asr_voice("/Users/hamburger/Documents/AI/music/output.wav"))