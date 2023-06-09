import logging
import os
from datetime import datetime
import openai

from util.es.es import es
from util.redis.redis_client import api_key_manager
from openai_util.prompt import get_message_important_score
from openai_util.gpt4.stream_ship import chat_use_stream_ship

# 保存日志
logger = logging.getLogger(__name__)


def query_by_node_id(node_id_list, creator):
    query_body = {
        "query": {
            "bool": {
                "should": [
                    {"terms": {"parent_id": node_id_list}},
                    {"terms": {"content_node_id": node_id_list}}
                ],
                "minimum_should_match": 1
            }
        },
        "sort": [
            {"content_creation_time": {"order": "asc"}}
        ]
    }

    return es.search(index="lang_chat_content", body=query_body)


#  查询相关的文本内容
def query_vector_to_string(content, query_vector, content_owner, ip):
    query_body = None
    if content_owner and content_owner != "default":
        # 定义查询
        query_body = {
            "size": 3,
            "query": {
                "function_score": {
                    "query": {
                        "term": {
                            "content_creator": content_owner
                        }
                    },
                    "score_mode": "sum",
                    "boost_mode": "replace",
                    "functions": [
                        {
                            "filter": {"match": {
                                "generated_content": {
                                    "query": content
                                }
                            }},
                            "script_score": {
                                "script": {
                                    "source": "1 / (1 + Math.exp(-_score / 10.0))"
                                }
                            }
                        },
                        {
                            "filter": {"match_all": {}},
                            "exp": {
                                "content_last_access_time": {
                                    "scale": "1h",
                                    "decay": 0.5
                                }
                            }
                        },
                        {
                            "filter": {"match_all": {}},
                            "field_value_factor": {
                                "field": "content_importance",
                                "missing": 0
                            }
                        },
                        {
                            "filter": {"match_all": {}},
                            "script_score": {
                                "script": {
                                    "source": "(cosineSimilarity(params.query_vector, 'content_vector') + 1.0) / 2.0",
                                    "params": {
                                        "query_vector": query_vector
                                    }
                                }
                            }
                        }
                    ]
                }
            },
            "sort": [
                {"content_creation_time": {"order": "desc"}}
            ]
        }
    elif ip:
        query_body = {
            "size": 3,
            "query": {
                "function_score": {
                    "query": {
                        "match": {
                            "creator_ip": ip
                        }
                    },
                    "score_mode": "sum",
                    "boost_mode": "replace",
                    "functions": [
                        {
                            "filter": {"match": {
                                "generated_content": {
                                    "query": content
                                }
                            }},
                            "script_score": {
                                "script": {
                                    "source": "1 / (1 + Math.exp(-_score / 10.0))"
                                }
                            }
                        },
                        {
                            "filter": {"match_all": {}},
                            "exp": {
                                "content_last_access_time": {
                                    "scale": "1h",
                                    "decay": 0.5
                                }
                            }
                        },
                        {
                            "filter": {"match_all": {}},
                            "field_value_factor": {
                                "field": "content_importance",
                                "missing": 0
                            }
                        },
                        {
                            "filter": {"match_all": {}},
                            "script_score": {
                                "script": {
                                    "source": "(cosineSimilarity(params.query_vector, 'content_vector') + 1.0) / 2.0",
                                    "params": {
                                        "query_vector": query_vector
                                    }
                                }
                            }
                        }
                    ]
                }
            },
            "sort": [
                {"content_creation_time": {"order": "desc"}}
            ]
        }
    else:
        logger.warning("query_vector_to_string: content_owner and ip are both None")
        return None
    return es.search(index="lang_chat_content", body=query_body)


def chat_with_single_msg(content):
    openai.api_key = api_key_manager.get_openai_key()
    try:
        prompt_msg = get_message_important_score(content)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{'role': 'user', 'content': prompt_msg}],
            temperature=0,
        )
        return response['choices'][0]['message']['content']
    except openai.OpenAIError as e:
        logger.exception(e)
        return e


def get_msg_important_score(content):
    score = chat_use_stream_ship(get_message_important_score(content))
    try:
        return float(score)
    except ValueError:
        return 0


# 插入文档
def insert_history(content_node_id, parent_id, creator_ip, content_owner, creator, content, content_vector):
    # 使用OpenAI的embedding生成向量
    try:
        # 获取当前时间
        current_time = datetime.now()
        score = 0
        if os.getenv('USE_IMPORTANT_SCORE', 'False') == 'True' and not 'gpt-3.5' == creator:
            score = get_msg_important_score(content)

        # 创建文档
        doc = {
            "content_node_id": content_node_id,
            "content_leaf_depth": 0,  # 这里假设叶子深度为0，你可以根据需要进行修改
            "content_creator": creator,  # 这里假设内容创建者为"creator"，你可以根据需要进行修改
            "content_creation_time": current_time,
            "content_last_access_time": current_time,
            "generated_content": content,
            "content_importance": float(score),
            "content_type": 1,
            "content_vector": content_vector,
            "content_owner": content_owner,
            "creator_ip": creator_ip,
            "parent_id": parent_id
        }
        docId = content_owner + "_" + content_node_id
        # 插入文档
        res = es.index(index="lang_chat_content", body=doc, id=docId)
        return res
    except Exception as e:
        logger.info(e)
