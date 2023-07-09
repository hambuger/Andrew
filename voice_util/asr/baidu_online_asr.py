import json
from functools import lru_cache

from voice_util.asr.voice_asr import VoiceAsr
import wave
import requests


@lru_cache(maxsize=1)
def fetch_token():
    token_url = "http://openapi.baidu.com/oauth/2.0/token"
    body = {
        "grant_type": "client_credentials",
        "client_id": "zNCNuwvB8tLRdGPNvKR2WH5w",
        "client_secret": "quhwG9c3i0418KvS3oWxnxk1gHPPMu7k",
    }
    try:
        req = requests.post(
            token_url,
            headers={"Content-Type": "application/json; charset=UTF-8"},
            data=body,
        )
        s = req.content.decode("utf-8", "ignore")
        result = json.loads(s)
        return result["access_token"]
    except Exception as err:
        print(f"请求token_access失败: {err}")


def baidu_asr(file, file_type='pcm', sample_rate=16000):
    asr_url = "http://vop.baidu.com/pro_api"
    length = len(file)
    if length == 0:
        print(f"这个语音文件 {file} 是空的")
    headers = {
        "Content-Type": "audio/" + file_type + ";rate=" + str(sample_rate),
        "Content-Length": str(length),
    }
    params = {"cuid": "hamburger-Robot", "token": fetch_token(), "dev_pid": 80001}

    try:
        req = requests.post(asr_url, params=params, headers=headers, data=file)
        s = req.content.decode("utf-8")
        res = json.loads(s)
        if res["err_no"] == 0:
            return "".join(res["result"])
        else:
            if res["err_msg"] == "request pv too much":
                print("       出现这个原因很可能是你的百度语音服务调用量超出限制，或未开通付费")
            return ""
    except Exception as err:
        print(f"百度ASR极速版请求失败: {err}")
        return ""


class OnlineAsr(VoiceAsr):
    def asr_voice(self, voice_file, language='zh'):
        with wave.open(voice_file, "rb") as audio_file:
            return baidu_asr(file=audio_file.readframes(audio_file.getnframes()))

# print(OnlineAsr().asr_voice("/Users/hamburger/Documents/AI/music/output.wav"))
