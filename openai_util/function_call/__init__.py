# load class on initialization
from openai_util.function_call import funcation_invoke, openaifunc_decorator, register_function  # noqa: F401

# picture recognition
from image_util import image_recognition, picture_get, play_video  # noqa: F401

# play music
from voice_util.play_song import play_song_with_qq_music  # noqa: F401

# search
from info_util.google_serper import query_info_from_google  # noqa: F401

# Call up
from phone_util.call.call_util import call_someone  # noqa: F401

# Check the weather
from info_util.weather_query import get_weather  # noqa: F401

# The python code runs
from code_util.run_python import run_python_code  # noqa: F401

# wolframalpha
from info_util.wolfram_alpha_util import query_wolframalpha  # noqa: F401

# position
from info_util.location import get_my_location_city  # noqa: F401

# download file
from info_util.download import download_file_from_url  # noqa: F401

# generate image
from image_util.image_text import text_to_image  # noqa: F401

# learned skills
import learn_skill  # noqa: F401

# pip install
from code_util.pip_install import install_modules  # noqa: F401

# Learn new skills and form non-representative memories
from code_util.learn2 import learn_and_save_as_skill, save_method_code  # noqa: F401
