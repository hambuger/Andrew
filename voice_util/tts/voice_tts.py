import os
import pyttsx3

engine = None
is_playing = False
stream = None
p = None
os_name = os.getenv('os_name', 'windows')
if os_name == 'windows':
    import win32com.client

    engine = win32com.client.Dispatch('SAPI.SPVoice')
elif os_name == 'macos':
    engine = pyttsx3.init()
elif os_name == 'linux':
    import asyncio
    from pydub import AudioSegment
    import pyaudio
    from pydub.utils import make_chunks
    import edge_tts
    from paddlespeech.cli.tts.infer import TTSExecutor

    engine = TTSExecutor()

output_path = 'tmp/output.wav'

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
        global is_playing, stream, p
        is_playing = True
        communicate = edge_tts.Communicate(text, 'zh-CN-YunyangNeural')
        asyncio.run(communicate.save(output_path))
        p = pyaudio.PyAudio()
        seg = AudioSegment.from_file(output_path)
        stream = p.open(format=p.get_format_from_width(seg.sample_width),
                        channels=seg.channels,
                        rate=seg.frame_rate,
                        output=True)

        # Just in case there were any exceptions/interrupts, we release the resource
        # So as not to raise OSError: Device Unavailable should play() be used again
        try:
            # break audio into half-second chunks (to allows keyboard interrupts)
            for chunk in make_chunks(seg, 500):
                if not is_playing:
                    break
                stream.write(chunk._data)
        except BaseException as e:
            pass
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
        # 音频播放完成后，重置 is_playing 标记
        is_playing = False


def stop_speak():
    if os_name == 'windows':
        if engine.Status.RunningState == 2:
            engine.Speak('', 2)
            while engine.Status.RunningState != 1:
                pass  # 等待语音输出完全停止while engine.Status.RunningState != 1:
    elif os_name == 'macos':
        engine.stop()
    elif os_name == 'linux':
        global is_playing, stream, p
        if is_playing:
            # 在播放时停止音频播放
            stream.stop_stream()
            is_playing = False
