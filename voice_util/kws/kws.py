import time
import struct
import wave
from collections import deque

import pvporcupine
import pyaudio


def picovoice(save_file_path: str):
    picovoice_access_key = 'oH7xQFgfFONcVY2ll3a7p07sxBBvZqd6dy116lzeig4a2UGmE0+EtQ=='
    porcupine = pvporcupine.create(
        access_key=picovoice_access_key,
        keyword_paths=['安德鲁_zh_windows_v2_2_0.ppn', '安德鲁_zh_windows_v2_2_1.ppn'],
        model_path='porcupine_params_zh.pv'
    )
    pa = pyaudio.PyAudio()
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length)

    frames = []  # Store audio data here
    buffer_length = 50  # Buffer the last 50 frames
    frame_buffer = deque(maxlen=buffer_length)
    record_seconds_after_wakeup = 5  # Record for 5 seconds after wakeup
    recording = False
    start_time = None

    while True:
        pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
        _pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
        keyword_index = porcupine.process(_pcm)

        frame_buffer.append(pcm)

        if keyword_index >= 0:
            recording = True
            frames.extend(list(frame_buffer))  # Add buffer to frames
            start_time = time.time()

        if recording and time.time() - start_time > record_seconds_after_wakeup:
            break

    audio_stream.stop_stream()
    audio_stream.close()
    pa.terminate()
    porcupine.delete()

    # Save audio to a WAV file
    with wave.open(save_file_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
        wf.setframerate(porcupine.sample_rate)
        wf.writeframes(b''.join(frames))
