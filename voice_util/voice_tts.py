from paddlespeech.cli.tts.infer import TTSExecutor

import os
import subprocess

tts = TTSExecutor()


def file_2_audio(text, output="output.wav", voice_play=False):
    tts(am="fastspeech2_male", voc="pwgan_male", text=text, output=output, use_onnx=True)
    if voice_play:
        os_name = os.getenv('os_name', 'macos')
        if os_name == 'macos':
            subprocess.run(["say", text])
        else:
            import sounddevice as sd
            import soundfile as sf
            data, fs = sf.read(output)
            sd.play(data, fs)
            sd.wait()
