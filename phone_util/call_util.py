import time

from appium import webdriver
from appium.webdriver.common.mobileby import MobileBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openai_util.function_call.openaifunc_decorator import openai_func
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(10)


@openai_func
def call_someone(name: str):
    """
    call someone
    :param name: The name of the contact to call
    """
    executor.submit(call, name)
    return "正在呼叫：{}".format(name)


def call(name):
    desired_caps = {
        'platformName': 'Android',
        'platformVersion': '10.0.0',
        # 'deviceName': '192.168.2.104:5555',
        'deviceName': 'P7CDU18119007423',
        'noReset': True,
        'automationName': 'UiAutomator2',
        'appPackage': 'com.android.contacts',
        'appActivity': 'com.android.contacts.activities.DialtactsActivity',
        'adbExecTimeout': 30000
    }

    driver = webdriver.Remote('http://127.0.0.1:4723', desired_caps)
    driver.press_keycode(3)
    time.sleep(3)
    driver.press_keycode(3)
    wait = WebDriverWait(driver, 10)

    wait.until(EC.presence_of_element_located((MobileBy.XPATH, '//android.widget.TextView[@text="电话"]'))).click()
    time.sleep(1)
    wait.until(EC.presence_of_element_located((MobileBy.XPATH, '//android.widget.TextView[@text="联系人"]'))).click()
    wait.until(
        EC.presence_of_element_located((MobileBy.XPATH, f"""//android.widget.TextView[@text="{name}"]"""))).click()
    wait.until(
        EC.presence_of_element_located((MobileBy.ID, 'com.android.contacts:id/primary_action_call_button'))).click()
    driver.quit()

# call_someone("爸")
