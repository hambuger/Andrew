# 导入logging模块
import logging
import os
# 导入工具
import sys
import time

import tiktoken
from dotenv import load_dotenv
# 导入flask模块
from flask import Flask, render_template, request, session

# 导入openai模块
import openai
from blog.blog import blog_route
from excel.excel import excel_route
from openai_util.chat import chat_route
from util.redis.redis_client import api_key_manager
import openai_util.prompt as prompt

# 创建一个flask应用
app = Flask(__name__)
# 加载配置文件
load_dotenv()
# 导入并注册路由
app.register_blueprint(excel_route)
app.register_blueprint(blog_route)
app.register_blueprint(chat_route)
# 设置一个密钥，用于保存session
app.secret_key = os.getenv('APP_SECRET_KEY')
# 保存日志
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s [Line: %(lineno)d]: %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p'
)


def append_session(input_msg):
    try:
        # 获取session的值
        session_value = request.cookies.get("session")
        # 获取session的大小（字节）
        session_size = sys.getsizeof(session_value)
        # 如果session的大小超过4KB，将history里的内容取一半处理
        if session_size > 1000:
            # 获取history对象数组
            history = session["history"]
            # 计算数组的长度
            length = len(history)
            # 取数组的后一半
            half = history[length // 2:]
            # 用后一半替换原来的history
            session["history"] = half
            session.modified = True
        session['history'].append(input_msg)
        session.modified = True
        return "OK"
    except Exception:
        return "Something went wrong"


# 调用chatgpt对话
def chat():
    openai.api_key = api_key_manager.get_key()
    try:
        # 调用chatgpt3.5模型，传入对话列表
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=session['history']
        )
        return response
    except openai.error.RateLimitError:
        return "等会再聊，我太忙了"
    except Exception as e:
        logging.error("chat error" + str(e))
        return None


def hgchat():
    openai.api_key = api_key_manager.get_gh_chat_model_key()
    try:
        # 调用chatgpt3.5模型，传入对话列表
        response = openai.Completion.create(
            model=os.getenv("MY_CHAT_MODEL"),
            prompt=prompt.get_hg_prompt(session['history']),
            max_tokens=500,
            temperature=0.4,
            stop=["end"]
        )
        return response
    except Exception as e:
        logging.info("hgchat error" + str(e))
        return None


# 定义一个路由，用于显示主页面
@app.route('/')
def index():
    # 如果session中没有history，就创建一个空列表，用于保存用户的对话历史
    if 'history' not in session:
        session['history'] = []
    # 渲染一个模板，传入用户和chatgpt的默认头像和对话历史
    return render_template('index.html', user_avatar='user.png', chatgpt_avatar='chatgpt.png',
                           history=session['history'])


# 定义一个路由，用于处理用户的输入
@app.route('/input', methods=['POST'])
def input_msg():
    # 获取用户的输入
    user_input = request.form.get('user_input')
    # 如果用户的输入不为空
    if user_input:
        # 获取当前时间，格式化为字符串
        current_time = time.strftime('%A %B, %d %Y %H:%M:%S')
        # 获取当前用户的ip，如果有代理，使用HTTP_X_FORWARDED_FOR头部，否则使用remote_addr属性
        user_ip = request.headers.get('HTTP_X_FORWARDED_FOR')
        ip2 = request.remote_addr;
        ip3 = request.headers.get('REMOTE-HOST')
        if not user_ip or user_ip == '127.0.0.1':
            if not ip3 or ip3 == '127.0.0.1':
                user_ip = ip2
            else:
                user_ip = ip3
        # 打印当前时间和用户的ip，用加号连接
        logging.info(current_time + "====IP:" + user_ip + "====userContent:" + user_input)
        # 把用户的输入添加到对话历史中
        append_session({'role': 'user', 'content': user_input})
        session.modified = True
        # 用openai的聊天api生成一个回复
        chatgpt_reply = hgchat()
        # 如果回复不为空
        getContent = ""
        if chatgpt_reply:
            # 把chatgpt的回复添加到对话历史中
            getContent = chatgpt_reply['choices'][0]['text']
            append_session({'role': 'assistant', 'content': getContent})
            session.modified = True
        else:
            getContent = "等会再聊，我太忙了"
        return getContent
    else:
        return ""
