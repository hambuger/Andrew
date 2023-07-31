# 初始化时加载类
from openai_util.function_call import funcation_invoke, openaifunc_decorator, register_function  # noqa: F401

# 图片识别
from image_util import image_recognition, picture_get, play_video  # noqa: F401

# 播放音乐
from voice_util.play_song import play_song_with_qq_music  # noqa: F401

# 搜索
from info_util.google_serper import query_info_from_google  # noqa: F401

# 打电话
from phone_util.call.call_util import call_someone  # noqa: F401

# 查询天气
from info_util.weather_query import get_weather  # noqa: F401

# python代码运行
from code_util.run_python import run_python_code  # noqa: F401

# wolframalpha
from info_util.wolfram_alpha_util import query_wolframalpha  # noqa: F401

# 定位
from info_util.location import get_my_location_city  # noqa: F401

# 下载文件
from info_util.download import download_file_from_url  # noqa: F401

# 生成图片
from image_util.image_text import text_to_image  # noqa: F401
