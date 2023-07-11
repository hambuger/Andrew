# 初始化时加载类
from openai_util.function_call import funcation_invoke, openaifunc_decorator, register_function
# 图片识别
from image_util import image_recognition, picture_get, play_video
# 播放音乐
from voice_util.play_song import play_song_with_qq_music
# 搜索
from info_util.google_serper import query_info_from_google
# 打电话
from phone_util.call.call_util import call_someone
# 查询天气
from info_util.weather_query import get_weather
# python代码运行
from code_util.run_python import run_python_code