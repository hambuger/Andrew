import json
from config.global_logger import logger
import os
import time
from datetime import datetime
import openai
from redis.exceptions import WatchError

from util.es.es import es
from util.redis.redis_client import api_key_manager
from openai_util.prompt import get_message_important_score,extract_information_from_messages
from openai_util.gpt4.stream_ship import chat_use_stream_ship
from uuid import uuid4
from openai_util.embedding import get_embedding
from openai_util.sum_token import sum_text_token
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(10)


def query_by_node_id(node_id_list):
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
                                    "source": "double score = 1 / (1 + Math.exp(-_score / 10.0)); return score > 0.5 ? score : 0;"
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
                                    "source": "double score = (cosineSimilarity(params.query_vector, 'content_vector') + 1.0) / 2.0; return score > 0.25 ? score : 0;",
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
                {"content_leaf_depth": {"order": "desc"}},
                "_score"
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
                                    "source": "double score = 1 / (1 + Math.exp(-_score / 10.0)); return score > 0.5 ? score : 0;"
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
                                    "source": "double score = (cosineSimilarity(params.query_vector, 'content_vector') + 1.0) / 2.0; return score > 0.25 ? score : 0;",
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
                {"content_leaf_depth": {"order": "desc"}},
                "_score"
            ]
        }
    else:
        logger.warning("query_vector_to_string: content_owner and ip are both None")
        return None
    return es.search(index="lang_chat_content", body=query_body)


def query_vector_to_string_v2(content, query_vector, content_owner, ip):
    must_query = {}
    if content_owner and content_owner != "default":
        must_query = {"term": {"content_creator": content_owner}}
    elif ip:
        must_query = {"term": {"creator_ip": ip}}
    else:
        logger.warning("query_vector_to_string: content_owner and ip are both None")
        return None
    # 定义查询
    query_body = {
        "size": 3,
        "query": {
            "function_score": {
                "query": {
                    "bool": {
                        "must": [
                            must_query
                        ]
                    }
                },
                "functions": [
                    {
                        "filter": {
                            "match": {
                                "generated_content": content
                            }
                        },
                        "script_score": {
                            "script": {
                                "source": "_score / (1 + _score)"
                            }
                        }
                    },
                    {
                        "gauss": {
                            "content_last_access_time": {
                                "origin": "now",
                                "scale": "24h",
                                "offset": "1h",
                                "decay": 0.5
                            }
                        }
                    },
                    {
                        "field_value_factor": {
                            "field": "content_importance"
                        }
                    },
                    {
                        "script_score": {
                            "script": {
                                "source": "1 / (1 + Math.exp(-1.0 * doc['content_leaf_depth'].value))"
                            }
                        }
                    },
                    {
                        "filter": {"match_all": {}},
                        "script_score": {
                            "script": {
                                "source": "double score = (cosineSimilarity(params.query_vector, 'content_vector') + 1.0); return score > 0.5 ? 10 + score : 0;",
                                "params": {
                                    "query_vector": query_vector
                                }
                            }
                        }
                    }
                ],
                "score_mode": "sum",
                "boost_mode": "replace",
                "min_score": 10
            }
        }
    }

    return es.search(index="lang_chat_content", body=query_body)


def chat_with_single_msg(content):
    openai.api_key = api_key_manager.get_openai_key()
    try:
        prompt_msg = get_message_important_score(content)
        response = openai.ChatCompletion.create(
            model=os.getenv('DEFAULT_CHAT_MODEL', 'gpt-3.5-turbo'),
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
def get_leaf_sum_content_list(r_content_list):
    if r_content_list:
        try:
            prompt = extract_information_from_messages(''.join(r_content_list))
            extract_info_str = chat_use_stream_ship(prompt)
            logger.info("extract_info_str: %s", extract_info_str)
            if extract_info_str:
                return json.loads(extract_info_str)
        except Exception:
            logger.exception("get_leaf_sum_content_list error")
            return []
    else:
        return []


def insert_history(content_node_id, parent_id, creator_ip, content_owner, creator, content, content_vector,
                   content_leaf_depth, depend_node_ids):
    # 使用OpenAI的embedding生成向量
    try:
        # 获取当前时间
        current_time = datetime.now()
        score = 0
        if os.getenv('USE_IMPORTANT_SCORE', 'False') == 'True' and not 'gpt-3.5' == creator:
            score = get_msg_important_score(content)
        content_type = 1
        if content_leaf_depth > 0:
            content_type = 2

        # 创建文档
        doc = {
            "content_node_id": content_node_id,
            "content_leaf_depth": content_leaf_depth,  # 这里假设叶子深度为0，你可以根据需要进行修改
            "content_creator": creator,  # 这里假设内容创建者为"creator"，你可以根据需要进行修改
            "content_creation_time": current_time,
            "content_last_access_time": current_time,
            "generated_content": content,
            "content_importance": float(score),
            "content_type": content_type,
            "content_vector": content_vector,
            "content_owner": content_owner,
            "creator_ip": creator_ip,
            "parent_id": parent_id,
            "depend_node_id": depend_node_ids
        }
        docId = content_owner + "_" + content_node_id
        # 插入文档
        es.index(index="lang_chat_content", body=doc, id=docId)
        # 检查是否需要归纳历史聊天
        gpt_flag = 'gpt-3.5' == creator
        if not creator == 'default':
            try_add_extract_info_from_leaf(content_node_id, content, content_leaf_depth, content_owner, creator, creator_ip, gpt_flag)
    except Exception as e:
        logger.exception(e)
        logger.info(e)


def try_add_extract_info_from_leaf(content_node_id, content, content_leaf_depth, content_owner, creator, creator_ip,
                                   gpt_flag):
    current_leaf_context_list_key = content_owner + "_leaf_" + str(content_leaf_depth) + "_text_list"
    for i in range(5):  # 尝试执行 5 次
        try:
            # WATCH 列表和长度值
            api_key_manager.r.watch(current_leaf_context_list_key)
            r_content_list = api_key_manager.r.lrange(current_leaf_context_list_key, 0, -1)
            r_content_list = [item.decode() for item in r_content_list]
            after_len = sum_text_token(r_content_list)
            # gpt4最大token为8000，留给gpt回答1000个，单次用户输入最大为3000token
            if after_len > 4000:
                api_key_manager.r.delete(current_leaf_context_list_key)
                executor.submit(insert_extract_info_list, content_leaf_depth, content_owner, creator,
                                creator_ip, r_content_list)
            save_r_content = ''
            if content_leaf_depth == 0:
                save_r_content = '(' + content_node_id + ')' + 'USER:' + content + '\n'
                if gpt_flag:
                    save_r_content = '(' + content_node_id + ')' + 'AI:' + content + '\n'
            else:
                save_r_content = '(' + content_node_id + ')' + content + '\n'
            # 开始一个事务
            pipe = api_key_manager.r.pipeline()
            # 将rpush操作添加到事务
            pipe.rpush(current_leaf_context_list_key, save_r_content)
            # 尝试执行事务
            pipe.execute()
            # 如果事务成功执行，跳出循环
            break
        except WatchError:
            # 其他客户端改变了 WATCH 的键，事务被打断
            logger.warning("Concurrent modification, retrying...")
            time.sleep(1)  # 等待一秒然后重试
        except Exception as e:
            logger.exception(e)
            break
        finally:
            api_key_manager.r.unwatch()  # 清除 WATCH


def insert_extract_info_list(content_leaf_depth, content_owner, creator, creator_ip, r_content_list):
    # 归纳历史聊天
    context_list = get_leaf_sum_content_list(r_content_list)
    # 将归纳插入到数据库
    if context_list:
        for context in context_list:
            context_vector = get_embedding(context["text"])
            context_node_id = str(uuid4())
            insert_history(context_node_id, "0", creator_ip, content_owner, creator,
                           context["text"],
                           context_vector, content_leaf_depth + 1,context["p_ids"])


def update_last_access_time(id_list):
    if id_list:
        for doc_id in id_list:
            if not doc_id:
                continue
            body = {
                "doc": {
                    "content_last_access_time": datetime.now()
                }
            }
            es.update(index='lang_chat_content', id=doc_id, body=body)
