import json
import logging
import os

import openai
from flask import request, Blueprint, Response
from openai import OpenAIError

from memory.remember import insert_history
from openai_util.msg_deal import generate_messages_v3
from util.redis.redis_client import api_key_manager
from openai_util.embedding import get_embedding
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(10)

chat_route = Blueprint('chat', __name__)

logger = logging.getLogger(__name__)


@chat_route.route('/v1/models', methods=['GET'])
def model():
    auth_info = request.headers.get('Authorization')
    set_req_api_key(auth_info)
    try:
        return openai.Model.list()
    except OpenAIError as e:
        logger.exception(e)
        return e.message


@chat_route.route('/v1/chat/completions', methods=['POST'])
def openai_chat_completions():
    try:
        # 获取传入参数
        (params, message_id, parent_id) = deal_request_param()
        # 保存聊天历史
        (userName, ip) = add_message_record(params, message_id, parent_id)
        # 在调用API时传入参数
        response = openai.ChatCompletion.create(**params)
        # 处理流式返回
        return deal_stream_response(params, response, message_id, userName, ip)
    except OpenAIError as e:
        logger.exception(e.message)
        return e.message
    except Exception as e:
        logger.exception("error: {}".format(e))
        return "未知错误，请联系hamburger"


# 设置请求的api_key
def set_req_api_key(auth_info):
    need_user_api_key = os.getenv('NEED_USER_API_KEY', False) == 'True'
    api_key = None
    if auth_info:
        api_key = auth_info.replace('Bearer ', '')
        if not need_user_api_key and (not api_key or not api_key.startswith('sk-')):
            api_key = api_key_manager.get_openai_key()
    elif not need_user_api_key:
        api_key = api_key_manager.get_openai_key()
    openai.api_key = api_key


# 插入用户的聊天记录
def add_message_record(params, message_id, parent_id):
    messages = params.get('messages')
    client_ip = request.headers.get('X-Forwarded-For', default=request.remote_addr)
    ip = request.json.get('ip') or client_ip
    userName = request.json.get('user_name') or 'default'
    if not message_id:
        return None, None
    content = messages[-1].get("content")
    content_vector = get_embedding(content)
    params['messages'] = generate_messages_v3(content, content_vector, userName, ip, messages)
    logger.info('messages: {}'.format(params['messages']))
    # 异步处理保存聊天记录
    executor.submit(insert_history, message_id, parent_id, ip, userName, userName, content, content_vector, 0, [])
    # 异步任务已启动，立即返回需要的值
    return userName, ip


# 插入GPT的返回记录
def add_response_record(all_contents, bot_msg_ids, parent_id, ip, user_name):
    content_vector = get_embedding(''.join(all_contents))
    insert_history(bot_msg_ids[0], parent_id, ip, user_name, 'gpt-3.5', ''.join(all_contents), content_vector, 0, [])


# 处理流式返回
def deal_stream_response(params, response, parent_id, user_name, ip):
    all_contents = []
    botMsgIds = []

    def stream_response():
        for chunk in response:
            content = chunk['choices'][0]['delta'].get('content', '')
            all_contents.append(content)
            botMsgIds.append(chunk['id'])
            yield 'data: ' + json.dumps(chunk) + '\n\n'
        executor.submit(add_response_record, all_contents, botMsgIds, parent_id, ip, user_name)

    if params.get('stream'):
        return Response(stream_response(), mimetype='application/octet-stream', content_type='application/json')
    else:
        return response


# 处理请求参数
def deal_request_param():
    # 获取api_key,判断是否需要使用系统api_key
    need_user_api_key = os.getenv('NEED_USER_API_KEY', False) == 'True'
    auth_info = request.headers.get('Authorization')
    api_key = None
    if auth_info:
        api_key = auth_info.replace('Bearer ', '')
        if not need_user_api_key and (not api_key or not api_key.startswith('sk-')):
            api_key = api_key_manager.get_openai_key()
    elif not need_user_api_key:
        api_key = api_key_manager.get_openai_key()
    openai.api_key = api_key
    # 获取接口参数
    req_model = request.json.get('model')
    messages_req = request.json.get('messages')
    message_id = messages_req[-1].get('id')
    parent_id = None
    if len(messages_req) > 1:
        parent_id = messages_req[-2].get('id')
    # 处理前端传入的特殊信息
    messages = [{k: v for k, v in msg.items() if k in ['role', 'content']} for msg in messages_req]
    # 存储所有需要检查的字段的名字
    fields_to_check = ['logit_bias', 'temperature', 'top_p', 'n', 'stream', 'stop', 'max_tokens', 'presence_penalty',
                       'frequency_penalty', 'user']
    # 准备API调用的必要参数
    params = {
        'model': req_model,
        'messages': messages,
    }
    # 遍历所有需要检查的字段
    for field in fields_to_check:
        # 使用 .get() 方法从 request.json 获取字段值
        field_value = request.json.get(field)
        # 如果获取到的字段值非 None，将其加入 params
        if field_value is not None:
            params[field] = field_value
    return params, message_id, parent_id
