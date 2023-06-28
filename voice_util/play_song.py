import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from openai_util.function_call.openaifunc_decorator import openai_func
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(10)


@openai_func
def play_song_with_qq_music(song_name: str):
    """
    使用qq音乐根据用户提示播放歌曲
    :param song_name: 歌曲名
    """
    executor.submit(play_song, song_name)
    return "正在播放歌曲：{}".format(song_name)


def play_song(song_name):
    options = webdriver.ChromeOptions()
    options.add_argument("user-data-dir=/Users/hamburger/Documents/web_driver_chrome")
    options.add_argument("--start-maximized")  # 最大化窗口
    options.add_argument("--no-sandbox")  # 禁用沙箱
    options.add_argument("--disable-dev-shm-usage")  # 禁用开发者模式
    driver_path = '/Users/hamburger/Documents/AI/tool/chromedriver'
    webdriver_service = Service(driver_path)
    driver = webdriver.Chrome(service=webdriver_service, options=options)
    # 导航到 QQ 音乐
    driver.get("https:/y.qq.com/")
    # 在搜索框中输入歌曲名
    search_field = driver.find_element(By.CLASS_NAME, "search_input__input")
    search_field.clear()
    # 输入并提交搜索请求
    search_field.send_keys(song_name)
    # 寻找并点击播放按钮
    play_button = driver.find_element(By.CLASS_NAME, "search_input__btn")
    play_button.click()
    time.sleep(3)  # 暂停 3 秒
    play_button = driver.find_element(By.LINK_TEXT, "播放全部")
    play_button.click()
    time.sleep(3)  # 暂停 3 秒
    element = driver.find_elements(By.CLASS_NAME, "songlist__time")
    time_str = element[0].text
    # 分割字符串并转换成秒
    minutes, seconds = map(int, time_str.split(":"))
    total_seconds = minutes * 60 + seconds
    time.sleep(total_seconds)
    driver.quit()

# play_song_with_qq_music("六月的雨")
