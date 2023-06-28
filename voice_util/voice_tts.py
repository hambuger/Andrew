from paddlespeech.cli.tts.infer import TTSExecutor

tts = TTSExecutor()


def voice_2_file(text, output="output.wav", voice_play=False):
    tts(am="fastspeech2_male", voc="pwgan_male", text=text, output=output, use_onnx=True)
    if voice_play:
        import sounddevice as sd
        import soundfile as sf
        data, fs = sf.read(output)
        sd.play(data, fs)
        sd.wait()
