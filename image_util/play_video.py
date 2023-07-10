import json
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from youtube_search import YoutubeSearch
from openai_util.function_call.openaifunc_decorator import openai_func
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(10)


@openai_func
def play_video(query: str):
    """
    根据用户输入播放相应的视频
    :param query:用户查询
    :return:
    """
    executor.submit(inner_play, query)
    return "正在播放视频：{}".format(query)


def inner_play(query):
    results = YoutubeSearch(query, 1).to_json()
    data = json.loads(results)
    url_suffix_list = [video["url_suffix"] for video in data["videos"]]
    options = webdriver.ChromeOptions()
    options.add_argument(r"user-data-dir=D:\Python\Tools\chromedriver_win32\data")
    options.add_argument("--start-maximized")  # 最大化窗口
    options.add_argument("--no-sandbox")  # 禁用沙箱
    options.add_argument("--disable-dev-shm-usage")  # 禁用开发者模式
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    driver_path = r'D:\Python\Tools\chromedriver_win32\chromedriver'
    webdriver_service = Service(driver_path)
    driver = webdriver.Chrome(service=webdriver_service, options=options)
    # 打开播放页面
    driver.get("https://youtube.com" + url_suffix_list[0])
    # 定位到body元素，然后发送按键"f"
    time.sleep(2)
    body = driver.find_element(By.TAG_NAME, "body")
    body.send_keys('f')

    while True:
        try:
            # 获取播放器的状态
            player_status = driver.find_element(By.CSS_SELECTOR, ".html5-video-player").get_attribute("data-state")
            # 如果播放器的状态是"结束"，那么视频已经播放完成
            if player_status == "ended":
                driver.quit()
                break
        except Exception as e:
            print(f"An error occurred: {e}")
            break
        # 每隔一段时间检查一次
        time.sleep(5)
