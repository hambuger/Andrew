# 导入flask模块
from flask import Flask, render_template, request, session, Response
# 导入openai模块
import openai
import sys
import time
# 导入logging模块
import logging
import json
from langchat import query_vector_to_string, insert_document, query_node_id_to_string
from keycache import ApiKeyManager
import numpy as np

# 创建一个flask应用
app = Flask(__name__)
# 设置一个密钥，用于保存session
app.secret_key = 'some_secret_key'
# 保存日志
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s [Line: %(lineno)d]: %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p'
)

# 初始化redis，保存keys
api_key_manager = ApiKeyManager()


# 定义一个函数，用于获取一个有效的openai的密钥
def get_valid_openai_key():
    key = api_key_manager.get_key()
    return key


def appendSession(input):
    try:
        # 获取session的值
        session_value = request.cookies.get("session")
        # 获取session的大小（字节）
        session_size = sys.getsizeof(session_value)
        # 如果session的大小超过4KB，将history里的内容取一半处理
        if session_size > 3000:
            # 获取history对象数组
            history = session["history"]
            # 计算数组的长度
            length = len(history)
            # 取数组的后一半
            half = history[length // 2:]
            # 用后一半替换原来的history
            session["history"] = half
            session.modified = True
        session['history'].append(input)
        session.modified = True
        return "OK"
    except Exception as e:
        return "Something went wrong"


# 调用chatgpt对话
def chat():
    openai.api_key = get_valid_openai_key()
    response = None
    ip = request.remote_addr
    try:
        # 调用chatgpt3.5模型，传入对话列表
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=session['history']
        )
        return response
    except openai.error.RateLimitError:
        return chat()


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
def input():
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
        logging.info("ip1:{}".format(user_ip))
        logging.info("ip2:{}".format(ip2))
        logging.info("ip3:{}".format(ip3))
        if not user_ip or user_ip == '127.0.0.1':
            if not ip3 or ip3 == '127.0.0.1':
                user_ip = ip2
            else:
                user_ip = ip3
        # 打印当前时间和用户的ip，用加号连接
        logging.info(current_time + "====IP:" + user_ip + "====userContent:" + user_input)
        # 把用户的输入添加到对话历史中
        appendSession({'role': 'user', 'content': user_input})
        session.modified = True
        # 用openai的聊天api生成一个回复
        chatgpt_reply = chat()
        # 把chatgpt的回复添加到对话历史中
        appendSession(chatgpt_reply['choices'][0]['message'])
        session.modified = True
        getContent = chatgpt_reply['choices'][0]['message']['content']
        logging.info(current_time + "====IP:" + user_ip + "====gptContent:" + getContent)
        return getContent
    else:
        return ""


# 定义一个路由，用于微信小程序请求和网页聊天请求

def generateNewContent(content, content_vector, creator):
    try:
        response = query_vector_to_string(content_vector, creator)
        if response['hits']['total']['value'] == 0:
            return content
        content_list = []
        node_id_list = []
        for i, hit in enumerate(response['hits']['hits']):
            # 将其按照需要的格式添加到列表中
            node_id_list.append(hit['_source'].get('content_node_id', ''))
            node_id_list.append(hit['_source'].get('parent_id', ''))
        node_id_list = list(filter(None, node_id_list))
        nodeResponse = query_node_id_to_string(node_id_list, creator)
        for j, hit2 in enumerate(nodeResponse['hits']['hits']):
            generated_content2 = hit2['_source'].get('generated_content', '')
            creator2 = hit2['_source'].get('content_creator', '')
            creatorTime = hit2['_source'].get('content_creation_time', '')
            content_list.append("(" + creatorTime + ") " + creator2 + ":" + generated_content2)
        result = ""
        for i, contentStr in enumerate(content_list):
            result = result + f"{i + 1}:{contentStr}" + "\n"

        result = "MEMORIES sorted in relevance:\n" + result + "\nBased on chat message history and memories(Don't reply that I have provided information, whether it is useful or not), respond to this message.\n" + "\"" + content + "\""
        return result
    except Exception as e:
        logging.info("generateNewContent error: {}".format(e))

@app.route('/v1/chat/completions', methods=['POST'])
def hangpt():
    client_ip = request.headers.get('X-Forwarded-For', default=request.remote_addr)
    # 获取body中的字段messages
    messages = request.json.get('messages')
    all_contents = []
    botMsgId = ''
    logging.info("messages: {}".format(messages))
    userName = request.json.get('user_name') or 'default'
    messageId = messages[-1].get("id")
    try:
        # stream为空则为false
        stream = request.json.get('stream') or False
        openai.api_key = get_valid_openai_key()
        parentId = messages[-2].get("id")
        content = messages[-1].get("content")
        for d in messages:
            d.pop("id", None)
        # 持久化对话信息
        embedding = openai.Embedding.create(input=[content], model="text-embedding-ada-002")
        content_vector = np.array(embedding["data"][0]["embedding"]).tolist()
        gpt_content = generateNewContent(content, content_vector, userName)
        logging.info("gpt_content: {}".format(gpt_content))
        messages[-1]['content'] = gpt_content
        insert_document(messageId, parentId, client_ip, userName, userName, content, 0.5, content_vector)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=stream
        )
        def stream_response():
            global botMsgId
            for chunk in response:
                content = chunk['choices'][0]['delta'].get('content', '')
                all_contents.append(content)
                botMsgId = chunk['id']
                yield 'data: ' + json.dumps(chunk) + '\n\n'
            embedding = openai.Embedding.create(input=[''.join(all_contents)], model="text-embedding-ada-002")
            content_vector = np.array(embedding["data"][0]["embedding"]).tolist()
            insert_document(botMsgId, messageId, client_ip, userName, 'gpt-3.5', ''.join(all_contents), 0.5,
                            content_vector)

        if stream:
            return Response(stream_response(), mimetype='application/octet-stream', content_type='application/json')
        else:
            return response
    except Exception as e:
        logging.error("error: {}".format(e))
        return "未知错误，请联系hamburger"



# 定义一个路由，用于微信小程序请求
@app.route('/v1/models', methods=['GET'])
def model():
    openai.api_key = get_valid_openai_key()
    try:
        return openai.Model.list()
    except openai.error.RateLimitError as e:
        logging.info(e)
        return e
