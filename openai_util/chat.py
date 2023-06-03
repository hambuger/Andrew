import json
import logging

import numpy as np
import openai
from flask import request, Blueprint, Response

from memory.remember import insert_history
from openai_util.msg_deal import generate_messages_v3
from util.redis.redis_client import api_key_manager

chat_route = Blueprint('chat', __name__)

logger = logging.getLogger(__name__)


@chat_route.route('/v1/models', methods=['GET'])
def model():
    openai.api_key = api_key_manager.get_key()
    try:
        return openai.Model.list()
    except openai.error.RateLimitError as e:
        logger.error(e)
        return e


@chat_route.route('/v1/chat/completions', methods=['POST'])
def hangpt():
    client_ip = request.headers.get('X-Forwarded-For', default=request.remote_addr)
    # 获取body中的字段messages
    messages = request.json.get('messages')
    all_contents = []
    botMsgId = ''
    logger.info("messages: {}".format(messages))
    userName = request.json.get('user_name') or 'default'
    messageId = messages[-1].get("id")
    ip = request.json.get('ip')
    try:
        # stream为空则为false
        stream = request.json.get('stream') or False
        openai.api_key = api_key_manager.get_key()
        parentId = messages[-2].get("id")
        content = messages[-1].get("content")
        for d in messages:
            d.pop("id", None)
        # 持久化对话信息
        embedding = openai.Embedding.create(input=[content], model="text-embedding-ada-002")
        content_vector = np.array(embedding["data"][0]["embedding"]).tolist()
        messages = generate_messages_v3(content, content_vector, userName, ip or client_ip, messages)
        # logging.info("gpt_content: {}".format(gpt_content))
        insert_history(messageId, parentId, ip or client_ip, userName, userName, content, 0.5, content_vector)
        logger.info("messages: {}".format(messages))
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
            insert_history(botMsgId, messageId, ip or client_ip, userName, 'gpt-3.5', ''.join(all_contents), 0.5,
                           content_vector)

        if stream:
            return Response(stream_response(), mimetype='application/octet-stream', content_type='application/json')
        else:
            return response
    except Exception as e:
        logger.error("error: {}".format(e))
        return "未知错误，请联系hamburger"
