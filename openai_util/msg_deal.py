import logging

from memory.remember import query_vector_to_string, query_by_node_id
from openai_util.prompt import generateChagGPTPrompt2, generateChagGPTPrompt
from openai_util.token import gpt_3_encoding as encoding

logger = logging.getLogger(__name__)


def sum_message_token(new_messages):
    tokens = 0
    for message in new_messages:
        tokens = tokens + len(encoding.encode(message["role"] + message["content"]))
    return tokens


# 第三个版本的prompt，将历史消息和提示放到system提示中
def generate_messages_v3(content, content_vector, creator, ip, messages):
    try:
        length = sum_message_token(messages)
        while length > 3000:
            messages = messages[len(messages) // 2:]
            length = sum_message_token(messages)
        response = query_vector_to_string(content, content_vector, creator, ip)
        if response and response['hits']['total']['value'] == 0:
            return messages
        content_list = []
        node_id_list = []
        for i, hit in enumerate(response['hits']['hits']):
            # 将其按照需要的格式添加到列表中
            node_id_list.append(hit['_source'].get('content_node_id', ''))
            node_id_list.append(hit['_source'].get('parent_id', ''))
        node_id_list = list(filter(None, node_id_list))
        nodeResponse = query_by_node_id(node_id_list, creator)
        for j, hit2 in enumerate(nodeResponse['hits']['hits']):
            generated_content2 = hit2['_source'].get('generated_content', '')
            creator2 = hit2['_source'].get('content_creator', '')
            creatorTime = hit2['_source'].get('content_creation_time', '')
            content_list.append("(" + creatorTime + ") " + creator2 + ":" + generated_content2)
        result = ""
        for i, contentStr in enumerate(content_list):
            result = result + f"{i + 1}:{contentStr}" + "\n"
            length = length + len(encoding.encode(contentStr))
            if length > 3000:
                break

        result = generateChagGPTPrompt2(result)
        messages.insert(0, {'role': 'system', 'content': result})
        return messages
    except Exception as e:
        logger.error("generate_messages_v3 error: {}".format(e))
        return messages


# 第二版本的prompt，将历史消息当成对话元素放在messages中
def generate_messages_v2(content, content_vector, creator, ip, messages):
    try:
        response = query_vector_to_string(content, content_vector, creator, ip)
        if response and response['hits']['total']['value'] == 0:
            return messages
        newMessages = messages[-2:]
        tokenNum = sum_message_token(newMessages)
        if tokenNum > 3000:
            return newMessages[:-1]
        for i, hit in enumerate(response['hits']['hits']):
            # 将其按照需要的格式添加到列表中
            user = 'assistant' if hit['_source'].get('content_creator', '') == 'gpt-3.5' else 'user'
            tokenNum = tokenNum + len(encoding.encode(user + hit['_source'].get('generated_content', '')))
            if tokenNum > 3000:
                return newMessages
            newMessages.insert(0, {'role': user, 'content': hit['_source'].get('generated_content', '')})
        otherMessages = messages[:-2]
        y = 3
        for message in otherMessages[::-1]:
            tokenNum = tokenNum + len(encoding.encode(message["role"] + message["content"]))
            if tokenNum > 3000:
                return newMessages
            newMessages.insert(-y, message)
            y = y + 1
        return newMessages

    except Exception as e:
        logger.info("generate_messages_v2 error: {}".format(e))
        return messages


# 第一版本的prompt：将历史消息的信息和提示放在user消息的最后一条中
def generate_messages_v1(content, content_vector, creator, ip, messages):
    try:
        response = query_vector_to_string(content, content_vector, creator, ip)
        if response and response['hits']['total']['value'] == 0:
            return messages
        content_list = []
        node_id_list = []
        for i, hit in enumerate(response['hits']['hits']):
            # 将其按照需要的格式添加到列表中
            node_id_list.append(hit['_source'].get('content_node_id', ''))
            node_id_list.append(hit['_source'].get('parent_id', ''))
        node_id_list = list(filter(None, node_id_list))
        nodeResponse = query_by_node_id(node_id_list, creator)
        for j, hit2 in enumerate(nodeResponse['hits']['hits']):
            generated_content2 = hit2['_source'].get('generated_content', '')
            creator2 = hit2['_source'].get('content_creator', '')
            creatorTime = hit2['_source'].get('content_creation_time', '')
            content_list.append("(" + creatorTime + ") " + creator2 + ":" + generated_content2)
        result = ""
        for i, contentStr in enumerate(content_list):
            result = result + f"{i + 1}:{contentStr}" + "\n"

        result = generateChagGPTPrompt(content, result)
        messages[-1]['content'] = result
        return messages
    except Exception as e:
        logger.info("generate_messages_v1 error: {}".format(e))

        return messages
