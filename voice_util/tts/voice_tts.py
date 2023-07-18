import os
import pyttsx3

engine = None
os_name = os.getenv('os_name', 'macos')
if os_name == 'windows':
    import win32com.client

    engine = win32com.client.Dispatch('SAPI.SPVoice')
elif os_name == 'macos':
    engine = pyttsx3.init()


def text_2_audio(text):
    if os_name == 'windows':
        engine.Speak(text, 19)
        while engine.Status.RunningState != 1:
            pass
    elif os_name == 'macos':
        engine.setProperty('rate', 120)
        engine.say(text)
        engine.runAndWait()


def stop_speak():
    if os_name == 'windows':
        if engine.Status.RunningState == 2:
            engine.Speak('', 2)
            while engine.Status.RunningState != 1:
                pass  # 等待语音输出完全停止while engine.Status.RunningState != 1:
    elif os_name == 'macos':
        engine.stop()
