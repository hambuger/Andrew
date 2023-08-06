import collections
import os
import time
import wave
from scipy.signal import resample
import numpy as np
import pvporcupine
import pyaudio
import webrtcvad
from database_util.redis.redis_client import api_key_manager

# set some parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
CHUNK_DURATION_MS = 30  # milliseconds per audio chunk
PADDING_DURATION_MS = 1000  # Silence duration, in milliseconds

NUM_PADDING_CHUNKS = int(PADDING_DURATION_MS / CHUNK_DURATION_MS)
# 0 is the least sensitive (ie the least voice activity is reported), 3 is the most sensitive (ie the most voice activity is reported)
vad = webrtcvad.Vad(0)

pa = pyaudio.PyAudio()
RATE = int(pa.get_default_input_device_info()["defaultSampleRate"])
# If the sampling rate is not in 8000 16000 32000 48000, set the sampling rate to 16000
if RATE not in [8000, 16000, 32000, 48000]:
    RATE = 16000
CHUNK_SIZE = int(RATE * CHUNK_DURATION_MS / 1000)
stream = pa.open(format=FORMAT,
                 channels=CHANNELS,
                 rate=RATE,
                 input=True,
                 start=True,
                 frames_per_buffer=CHUNK_SIZE)

# This key is not used for interface calls, but for one-time identity verification
picovoice_access_key = os.getenv("PICOVOICE_ACCESS_KEY")
model_dir = os.getenv('KWS_MODEL_DIR', os.getcwd())

porcupine = pvporcupine.create(
    access_key=picovoice_access_key,
    keyword_paths=[os.path.join(model_dir, 'andrew_zh_' + os.getenv('OS_NAME') + '_v2_2_0.ppn')],
    model_path=os.path.join(model_dir, 'porcupine_params_zh.pv'),
)
# Whether a speech ends
got_a_sentence = False

# Wake up the window size of the listener
ring_buffer = collections.deque(maxlen=NUM_PADDING_CHUNKS)
# Is there a voice overheard
triggered = False
# Buffer to hold audio frames
voiced_frames = []
# Are keywords detected?
keyword_detected = False
# Records the last time a valid input was detected
last_input_time = 0
# If no valid input is detected for a period of time, enter the standby state
idle_timeout = 30
user_input_str = None


def set_user_input_str(str):
    global user_input_str
    user_input_str = str


def get_audio(audio_active=False, file_path='tmp/audio.wav', last_time=0):
    global triggered, got_a_sentence, voiced_frames, ring_buffer, keyword_detected, last_input_time, idle_timeout, user_input_str
    if last_time != 0:
        last_input_time = last_time
    stream.start_stream()
    voiced_frames = []
    while True:
        if user_input_str and user_input_str != 'stop' and not audio_active:
            triggered = False
            voiced_frames = []
            keyword_detected = False
            got_a_sentence = False
            user_input_str = None
            return False
        chunk = stream.read(CHUNK_SIZE, exception_on_overflow=False)
        active = vad.is_speech(chunk, RATE)
        ring_buffer.append((chunk, active))
        # print("active: ", active)
        if not triggered:
            num_voiced = len([chunk for chunk, active in ring_buffer if active])
            # print("1 num_voiced: ", num_voiced)
            # print("1 len(ring_buffer): ", len(ring_buffer))
            if num_voiced > 0.5 * len(ring_buffer):
                # print('Triggered')
                triggered = True
                voiced_frames.extend([chunk for chunk, _ in ring_buffer])
                ring_buffer.clear()
                last_input_time = time.time()

        else:
            voiced_frames.append(chunk)

            num_unvoiced = len([chunk for chunk, active in ring_buffer if not active])
            # print("2 num_unvoiced: ", num_unvoiced)
            # print("2 len(ring_buffer): ", len(ring_buffer))
            if num_unvoiced > 0.9 * len(ring_buffer):  # 减小这个值
                # print('Voice end detected')
                got_a_sentence = True
                triggered = False
                ring_buffer.clear()
        # If no valid input is detected for a period of time, it enters the standby state
        if time.time() - last_input_time > idle_timeout:
            audio_active = False
            keyword_detected = False
            if api_key_manager.get_key_value('AUDIO_KEY') == os.getenv('OS_NAME'):
                api_key_manager.delete_key('AUDIO_KEY')
        if got_a_sentence:
            # print('Processing sentence')
            data = b''.join(voiced_frames)
            if not audio_active:
                # Convert the data to a numpy array of 16-bit PCM samples
                pcm_data = np.frombuffer(data, dtype=np.int16)
                if RATE != 16000:
                    # Resampled to 16kHz
                    original_duration = len(pcm_data) / RATE
                    pcm_data = resample(pcm_data, num=int(original_duration * 16000))
                # Iterate over all blocks, and process each block
                for i in range(0, len(pcm_data), porcupine.frame_length):
                    pcm_chunk = pcm_data[i:i + porcupine.frame_length]
                    # Make sure the block length is correct
                    if len(pcm_chunk) == porcupine.frame_length:
                        pcm_chunk = pcm_chunk.astype(np.int16)
                        result = porcupine.process(pcm_chunk)
                        if result >= 0:
                            keyword_detected = True
                            # print("Keyword Detected!")
                            break
            got_a_sentence = False
            voiced_frames = []
            # If keywords are detected, save the file
            if audio_active or keyword_detected:
                # print("Wake up!")
                keyword_detected = False
                if not api_key_manager.get_key_value('AUDIO_KEY'):
                    # No one is using it, try to acquire the lock
                    if api_key_manager.set_nx_key('AUDIO_KEY', os.getenv('OS_NAME'), 60 * 1000):
                        # Get the lock, you can use
                        # print("Device acquired the lock.")
                        pass
                    else:
                        #The lock has not been acquired, someone is using it
                        # print("Device did not acquire the lock. Another device is responding.")
                        audio_active = False
                        continue
                elif api_key_manager.get_key_value('AUDIO_KEY') != os.getenv('OS_NAME'):
                    # someone is using it, don't bother
                    # print("Device did not acquire the lock. Another device is responding2.")
                    audio_active = False
                    continue
                # write to a wav file
                wf = wave.open(file_path, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(pa.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(data)
                wf.close()
                break
    stream.stop_stream()
    return True
