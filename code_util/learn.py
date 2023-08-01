import json
import re
import subprocess

import openai
from openai_util.function_call.openaifunc_decorator import openai_func
from database_util.redis.redis_client import api_key_manager
from openai_util.function_call.funcation_invoke import get_invoke_method_info_by_name, \
    get_function_result_from_openai_response
from config.global_logger import logger

install_package = []


def check_and_install_modules_from_code(code):
    # 使用正则表达式匹配导入模块
    import_pattern = re.compile(r'\b(?:from|import)\s+(\w+(?:\.\w+)*)')
    modules_to_install = set(match.group(1) for match in import_pattern.finditer(code))

    # 检查并安装缺失的模块
    for module in modules_to_install:
        if module in install_package:
            continue
        try:
            __import__(module)
            logger.debug(f"{module} is already installed.")
            install_package.append(module)
        except ImportError:
            logger.debug(f"{module} is not installed. Installing...")
            try:
                subprocess.check_call(['pip', 'install', module])
                logger.debug(f"Successfully installed {module}.")
                install_package.append(module)
            except subprocess.CalledProcessError as e:
                logger.debug(f"Failed to install {module}. Error: {e}")


@openai_func
def learn_and_save_as_skill(skill_name: str):
    logger.debug('learn_and_save_as_skill')
    """
    Learn a new skill and save it as a skill.
    :param skill_name: The name of the skill to be learned.
    """
    openai.api_key = api_key_manager.get_openai_key()
    params = {

        "messages": [{"role": "user", "content": f'''
        生成一个python代码，其中包含一个函数，功能为{skill_name} 。
        你的返回只需要Python代码，不需要其他信息。
        '''}],
        "model": 'gpt-4',
        "temperature": 0
    }
    response = openai.ChatCompletion.create(**params)
    code_str = response['choices'][0]['message']['content']
    retry_count = 0
    while True:
        code_str_tmp = test_code(code_str, skill_name)
        logger.debug(code_str_tmp)
        if code_str_tmp == 'OK' or retry_count >= 10:
            break
        else:
            code_str = code_str_tmp
            retry_count += 1
    params = {

        "messages": [{"role": "user", "content": f'''
            根据下面的内容生成一个Python代码文件，保存在learn路径下，这个文件应该包含一个函数，功能为{skill_name}。
            ```
            {code_str}
            ```
            写入的方法需要加入注解@openai_func，并且生成方法注释，保证代码缩进，类似下面：
            from openai_util.function_call.openaifunc_decorator import openai_func\
            @openai_func\
            def function(param1: str, param2:str):\
                \'''\
                the method description\
                :param param1: the description of param1\
                :param param2: the description of param2\
                \'''\
                pass\
            '''}],
        "model": 'gpt-4',
        "temperature": 0,
        "functions": [get_invoke_method_info_by_name("run_python_code")],
        "function_call": {"name": "run_python_code"}
    }
    response2 = openai.ChatCompletion.create(**params)
    get_function_result_from_openai_response(response2)
    try:
        import learn_skill
    except Exception as e:
        logger.error(e)
    return "lean and save as skill successfully."


last_error = None


def test_code(code_str, skill_name):
    check_and_install_modules_from_code(code_str)
    openai.api_key = api_key_manager.get_openai_key()
    params = {
        "messages": [{"role": "user", "content": f'''
            验证下面的代码是否满足功能：{skill_name}
            ```
            {code_str}
            ```
            如果满足，直接回复一个单词'OK'，如果不满足，请修改代码并回复修改后的代码
            '''}],
        "model": 'gpt-4',
        "temperature": 0,
        "functions": [get_invoke_method_info_by_name("run_python_code")],
        "function_call": {"name": "run_python_code"}
    }
    response1 = openai.ChatCompletion.create(**params)
    function_name, function_result = get_function_result_from_openai_response(response1)
    global last_error
    if 'Error' in function_result:
        if function_result == last_error:
            function_result = function_result + ' 这是第二次出现这个错误，请仔细思考并且修改代码'
        last_error = function_result
    if function_result:
        params = {
            "messages": [{"role": "user", "content": f'''
                    验证下面的代码是否满足功能：{skill_name}
                    ```
                    {code_str}
                    ```
                    如果满足，直接回复一个单词'OK'，如果不满足，请修改代码并回复修改后的代码
                    '''}, response1['choices'][0]['message'], {"role": "function", "name": function_name,
                                                               "content": json.dumps(function_result)}],
            "model": 'gpt-4',
            "temperature": 0,
            "functions": [get_invoke_method_info_by_name("run_python_code")],
            "function_call": 'none'
        }
        response2 = openai.ChatCompletion.create(**params)
        return response2['choices'][0]['message']['content']
    return 'OK'

# learn_and_save_as_skill('获取当前时间的农历日期')
