# 导入flask模块
import os

from flask import Flask, render_template, request, session, Response
# 导入openai模块
import openai
import sys
import time
# 导入logging模块
import logging
import json
import hashlib
import tiktoken

from langchat import query_vector_to_string, insert_document, query_node_id_to_string
from keycache import ApiKeyManager
import numpy as np
from blog import query_data_by_id

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

encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")


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


def get_hg_prompt(param):
    prompt = ""
    # prompt":"韩家宝: 哪里呀\n龚琦: 旁边还有人露营 真羡慕\n韩家宝: 天气不错\n龚琦: 我到家了 嘿嘿\n韩家宝: 好\n龚琦: 明天要不要开电影呀\n我请你吃火锅哦\n###\n\n韩家宝: "
    for message in param:
        if message['role'] == 'user':
            prompt = prompt + "韩家宝: " + message['content'] + "\n"
        else:
            prompt = prompt + "龚琦: " + message['content'] + "\n"
    prompt = prompt + "###\n\n韩家宝: "
    print("prompt:{}".format(prompt))
    return prompt


def hgchat():
    openai.api_key = api_key_manager.get_gh_chat_model_key()
    try:
        # 调用chatgpt3.5模型，传入对话列表
        response = openai.Completion.create(
            model="ada:ft-personal:hamburger-2023-05-30-09-14-45",
            prompt=get_hg_prompt(session['history']),
            max_tokens=500,
            temperature=0.4,
            stop=["end"]
        )
        return response
    except Exception as e:
        logging.info("RateLimitError"+str(e))
        return hgchat()

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
        chatgpt_reply = hgchat()
        # 把chatgpt的回复添加到对话历史中
        getContent = chatgpt_reply['choices'][0]['text']
        appendSession({'role': 'assistant', 'content': getContent})
        session.modified = True
        logging.info("gptContent:" + getContent)
        return getContent
    else:
        return ""


# 定义一个路由，用于微信小程序请求和网页聊天请求

def generateChagGPTPrompt(content, result):
    prompt = f"The chat records that appear between the first ```` and last ```` are from the past. \n \
````{result}````\n \
Do not reveal in your reply that I have provided the above information.\n \
Based on chat history and memories, respond to the message between first <<< and last >>>.\n \
<<<{content}>>>"
    return prompt


def sumMessageToken(newMessages):
    tokens = 0
    for message in newMessages:
        tokens = tokens + len(encoding.encode(message["role"] + message["content"]))
    return tokens


def generateNewMessages(content_vector, creator, ip, messages):
    try:
        response = query_vector_to_string(content_vector, creator, ip)
        if response and response['hits']['total']['value'] == 0:
            return messages
        newMessages = messages[-2:]
        tokenNum = sumMessageToken(newMessages)
        if tokenNum > 4096:
            return newMessages[:-1]
        for i, hit in enumerate(response['hits']['hits']):
            # 将其按照需要的格式添加到列表中
            user = 'assistant' if hit['_source'].get('content_creator', '') == 'gpt-3.5' else 'user'
            tokenNum = tokenNum + len(encoding.encode(user + hit['_source'].get('generated_content', '')))
            if tokenNum > 4096:
                return newMessages
            newMessages.insert(0, {'role': user, 'content': hit['_source'].get('generated_content', '')})
        otherMessages = messages[:-2]
        y = 3
        for message in otherMessages[::-1]:
            tokenNum = tokenNum + len(encoding.encode(message["role"] + message["content"]))
            if tokenNum > 4096:
                return newMessages
            newMessages.insert(-y, message)
            y = y + 1
        return newMessages

    except Exception as e:
        logging.info("generateNewMessages error: {}".format(e))
        return messages


def generateNewContent(content, content_vector, creator, ip):
    try:
        response = query_vector_to_string(content_vector, creator, ip)
        if response and response['hits']['total']['value'] == 0:
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

        result = generateChagGPTPrompt(content, result)
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
    ip = request.json.get('ip')
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
        messages = generateNewMessages(content_vector, userName, ip or client_ip, messages)
        # logging.info("gpt_content: {}".format(gpt_content))
        # messages[-1]['content'] = gpt_content
        insert_document(messageId, parentId, ip or client_ip, userName, userName, content, 0.5, content_vector)
        logging.info("messages: {}".format(messages))
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
            insert_document(botMsgId, messageId, ip or client_ip, userName, 'gpt-3.5', ''.join(all_contents), 0.5,
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

@app.route('/blog/query', methods=['GET'])
def blog():
    id = request.args.get('id')
    parent_id = request.args.get('parentId')
    response = query_data_by_id(id, parent_id)
    logging.info(response)
    if not response:
        return None
    if id:
        if response['_source']:
            title = response['_source'].get('title', '')
            content = response['_source'].get('content', '')
            node_id = response['_source'].get('node_id', '')
            type = response['_source'].get('type', '')
            return {"title": title, "content": content, "id": node_id, "type": type}
        else:
            return None
    result = []
    if response and response['hits']['total']['value'] == 0:
        return result
    for index, hit in enumerate(response['hits']['hits']):
        title = hit['_source'].get('title', '')
        content = hit['_source'].get('content', '')
        node_id = hit['_source'].get('node_id', '')
        type = hit['_source'].get('type', '')
        result.append({"title": title, "content": content, "id": node_id, "type": type})
    return result


@app.route('/upload/image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return 'No image file found', 400

    image_file = request.files['image']
    if image_file.filename == '':
        return 'Invalid image file', 400
    save_directory = '/var/www/picture'
    # 使用 MD5 哈希函数生成唯一的字符串
    hash_object = hashlib.md5(image_file.filename.encode())
    hex_dig = hash_object.hexdigest()
    # 将哈希结果作为文件名
    filename = hex_dig + '.jpg'
    save_path = os.path.join(save_directory, filename)
    image_file.save(save_path)

    # 返回上传成功的响应，包含保存的图片路径
    image_url = '/picture/' + filename  # 替换为你的图片访问路径
    return {'message': 'Image uploaded successfully', 'url': image_url}
