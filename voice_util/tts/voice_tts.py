import os
import pyttsx3

engine = None
os_name = os.getenv('os_name', 'windows')
if os_name == 'windows':
    import win32com.client

    engine = win32com.client.Dispatch('SAPI.SPVoice')
elif os_name == 'macos':
    engine = pyttsx3.init()
elif os_name == 'linux':
    import asyncio
    from pydub import AudioSegment
    from pydub.playback import _play_with_pyaudio
    import edge_tts
    from paddlespeech.cli.tts.infer import TTSExecutor

    engine = TTSExecutor()

playback = None
is_playing = False


class AudioPlayer:

    def play(self, text):
        global playback, is_playing
        is_playing = True
        communicate = edge_tts.Communicate(text, 'zh-CN-YunyangNeural')
        asyncio.run(communicate.save('output.wav'))
        playback = _play_with_pyaudio(AudioSegment.from_file('output.wav'))
        # 音频播放完成后，重置 is_playing 标记
        is_playing = False

    def stop(self):
        global playback, is_playing
        if is_playing:
            # 在播放时停止音频播放
            print('stop')
            playback.stop()
            is_playing = False


def text_2_audio(text):
    if os_name == 'windows':
        engine.Speak(text, 19)
        while engine.Status.RunningState != 1:
            pass
    elif os_name == 'macos':
        engine.setProperty('rate', 120)
        engine.say(text)
        engine.runAndWait()
    elif os_name == 'linux':
        AudioPlayer().play(text)


def stop_speak():
    if os_name == 'windows':
        if engine.Status.RunningState == 2:
            engine.Speak('', 2)
            while engine.Status.RunningState != 1:
                pass  # 等待语音输出完全停止while engine.Status.RunningState != 1:
    elif os_name == 'macos':
        engine.stop()
    elif os_name == 'linux':
        AudioPlayer().stop()

# text_2_audio("你好，我是安德鲁")
