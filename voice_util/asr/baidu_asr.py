from voice_util.asr.voice_asr import VoiceAsr
from paddlespeech.cli.asr.infer import ASRExecutor

asr = ASRExecutor()


class ApiAsr(VoiceAsr):
    # Create an ASR executor

    def asr_voice(self, voice_file, language='zh'):
        return asr(model='conformer_wenetspeech', audio_file=voice_file, force_yes=True)


# begin = time.time()
# print(ApiAsr().asr_voice(r"C:\Users\Administrator\Desktop\share\output.wav") + "cost：" + str(time.time() - begin))
# begin = time.time()
# print(ApiAsr().asr_voice(r"C:\Users\Administrator\Desktop\share\zh.wav") + "cost：" + str(time.time() - begin))
# begin = time.time()
# print(ApiAsr().asr_voice(r"C:\Users\Administrator\Desktop\share\gongqi_1.wav") + "cost：" + str(time.time() - begin))
