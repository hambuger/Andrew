from concurrent.futures import ThreadPoolExecutor
from airtest.cli.parser import cli_setup
from airtest.core.api import *
from openai_util.function_call.openaifunc_decorator import openai_func

executor = ThreadPoolExecutor(10)


@openai_func
def call_someone(name: str):
    """
    call someone
    :param name: The name of the contact to call
    """
    executor.submit(call, name)
    return "正在呼叫：{}".format(name)


phone_os_name = os.getenv('PHONE_OS_NAME', 'android')


def call(name):
    if phone_os_name == 'android':
        return
    elif phone_os_name == 'ios':
        # import subprocess
        # def start_iproxy(local_port, device_port):
        #     return subprocess.Popen(['iproxy', str(local_port), str(device_port)])
        #
        #
        # # 开启 iproxy
        # iproxy_process = start_iproxy(8100, 8100)
        if not cli_setup():
            auto_setup(__file__, logdir=True, devices=["ios:///127.0.0.01:8100"])
        home()
        touch(Template(r"tpl1689055883401.png", record_pos=(-0.346, 0.929), resolution=(1170, 2532)))
        touch(Template(r"tpl1689055924886.png", record_pos=(0.002, 0.934), resolution=(1170, 2532)))
        touch(Template(r"tpl1689056082695.png", record_pos=(0.007, -0.664), resolution=(1170, 2532)))
        text(name)
        touch((146, 542))
        touch(Template(r"tpl1689057553922.png", record_pos=(-0.109, -0.408), resolution=(1170, 2532)))

# call_someone("爸")
