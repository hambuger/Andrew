import os
import pyttsx3
import subprocess

# 初始化语音引擎
engine = pyttsx3.init()
# 获取所有可用的语音
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)


def text_2_audio(text):
    # tts(am="fastspeech2_male", voc="pwgan_male", text=text, output=output, use_onnx=True)
    os_name = os.getenv('os_name', 'windows')
    if os_name == 'macos':
        subprocess.run(["say", text])
    else:
        engine.say(text)
        engine.runAndWait()
