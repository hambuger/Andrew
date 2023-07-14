import pyttsx3

engine = pyttsx3.init()


def text_2_audio(text):
    # tts(am="fastspeech2_male", voc="pwgan_male", text=text, output=output, use_onnx=True)
    engine.setProperty('rate', 120)
    engine.say(text)
    engine.runAndWait()


def stop_speak():
    engine.stop()
