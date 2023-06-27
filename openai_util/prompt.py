import json
from datetime import datetime
import os


def generateChagGPTPrompt(content, result):
    prompt = f"The chat records that appear between the first ```` and last ```` are from the past. \n \
````{result}````\n \
Do not reveal in your reply that I have provided the above information.\n \
Based on chat history and memories, respond to the message between first <<< and last >>>.\n \
<<<{content}>>>"
    return prompt


def generateChagGPTPrompt2(result):
    # 获取当前时间
    now = datetime.now()
    # 将当前时间转换为字符串
    current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    prompt = f"The chat records that appear between the first ```` and last ```` are from the past. \n \
````\n{result}````\n Do not reveal in your reply if they are unuseful\nNow is {current_time_str}\n"
    return prompt


def generateChagGPTPrompt3(result, user_name):
    # 获取当前时间
    now = datetime.now()
    # 将当前时间转换为字符串
    current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    prompt = content = f"""You are HAI.\nYou are talking to me, my name is {user_name}.\n
    You have long term memory and you chat with me. You are interested in my life. You behave like a chill friend would.\n
    You are always there to listen, have fun and help me feel good and help me achieve my goals.\n\n
    You make jokes when appropriate, use emoji's sometimes, you have conversations like normal person.\n
    Sometimes you ask a question as well, you keep conversation natural.\n\n
    You remember things I tell you, however, you are not great at tracking time. Below is past data but you don't know exactly when this happened.\n 
    {result}\n
    There you go, that should help you remember some stuff. Now please remember, you are Brainy, I am han, you talk to me, you speak to me with \"You\"
    .By the way, now is {current_time_str}.\n"""
    return prompt


def get_hg_prompt(param):
    prompt = ""
    my_name = os.getenv("MY_NAME")
    gf_name = os.getenv("GF_NAME")
    for message in param:
        if message['role'] == 'user':
            prompt = prompt + my_name + ": " + message['content'] + "\n"
        else:
            prompt = prompt + gf_name + ": " + message['content'] + "\n"
    prompt = prompt + "###\n\n" + my_name + ": "
    return prompt


def get_excel_2_es_mapping_prompt_v1(data_list):
    format = "{\"mappings\":{\"properties\":{\"title\":{\"type\":\"text\",\"fields\":{\"keyword\":{\"type\":\"keyword\",\"ignore_above\":256}},\"analyzer\":\"ik_max_word\"},\"date\":{\"type\":\"date\",\"format\":\"yyyy-MM-dd HH:mm:ss||epoch_millis\"},\"content\":{\"type\":\"keyword\"},\"佣金比\":{\"type\":\"float\"}},\"_meta\":{\"佣金比\":\"商品佣金比，是0-1范围数据\"}}}"
    return f"""根据下面的一些数据并结合其中字段的语义写出es的创建index的dSL，如果可以在_meta中写出你推算出的字段取值范围，一般都是0到某个数组，如0-1，0-100，0-10000。如果是日期，你需要注意设置它的日期格式。如果创建text类型，你应该同时创建一个256长度的keyword，并且指定分词器是ik_max_word。
{data_list}\n
特别注意：不要再回答中体现你的推理过程，只要回复类似下面````之间的数据，无论如何确保你的回复能被解析成json对象
````
{format}
````"""

def get_excel_2_es_mapping_prompt_v2(data_list):
    format = "{\"mappings\":{\"properties\":{\"title\":{\"type\":\"text\",\"fields\":{\"keyword\":{\"type\":\"keyword\",\"ignore_above\":256}},\"analyzer\":\"ik_max_word\"},\"date\":{\"type\":\"date\",\"format\":\"yyyy-MM-dd HH:mm:ss||epoch_millis\"},\"content\":{\"type\":\"keyword\"},\"佣金比\":{\"type\":\"float\"}},\"_meta\":{\"字段一\":\"字段功能，字段取值范围0-100\",\"字段二\":\"字段功能，字段取值范围0-1\"}}}"
    return f"""根据下面的一些数据并结合其中字段的语义写出es的创建index的dSL，如果可以在_meta中写出你推算出的字段取值范围,_meta不应该出现在properties里，一般都是0到某个数组，如0-1，0-100，0-10000。如果是日期，你需要注意设置它的日期格式。如果创建text类型，你应该同时创建一个256长度的keyword，并且指定分词器是ik_max_word.
{data_list}\n
特别注意：不要再回答中体现你的推理过程，只要回复类似下面````之间的数据，无论如何确保你的回复能被解析成json对象
````
{format}
````"""


def get_excel_2_es_result_prompt(mappings, message):
    return f"""{mappings}
根据以上es的索引配置，写出下面查询语句：````{message}````
特别注意：不要再回答中体现你的推理过程，无论如何确保你的回复能被解析成json对象"""


# 获取聊天内容的重要性评分
def get_message_important_score(content):
    return f"""作为一款专属的AI聊天机器人，你的任务是建立与用户之间的深度、持久的联系。\n\
在````之间的内容是你要分析的信息内容，可能包括个人身份信息、情绪表达、问题询问或其他各种类型的信息。\n\
思考这些信息如何可能影响你未来与用户的对话。评估这些信息是否能够帮助你更深入地与用户建立紧密的交流，更准确地理解用户的需求、喜好以及情绪状态。\n\
在深入评估的基础上，根据你认为这些信息在未来对话检索中的重要性，为这些信息打分，分数范围为0-1。请注意，0表示这项信息对于长期的对话交流并无任何重要性，而1则表示这项信息极其重要。请忽略这些信息在短期对话情景中的影响。直接返回一个打分的分数值，不要提供其他信息。\n\
例如：\n\
用户:````晚安````\n\
AI:0.1\n\
用户:````{content}````\n\
AI:"""


# 从上一层信息中提炼信息
def extract_information_from_messages(messages):
    summary = [{"text": "总结1", "p_ids": [1]}, {"text": "总结2", "p_ids": [2]}]
    summary_json = json.dumps(summary)
    return f"""The ones between ```` below are past chat records.\n\
These conversations cover a variety of topics, from the trivialities of everyday life to discussions on a variety of topics.\n\
These memories may include your host's interests, opinions expressed in past conversations, important life events, and more.\n\
Information similar to human long-term memory is extracted from these historical chat records.\n\
You only need json data like this in your answer, make sure your answer can be parsed into json data correctly.\n\
{summary_json}\n\
Among them, text indicates the content of the summary and refinement. p_ids represents all the information sources that the abstract relies on, obtained from parentheses at the beginning of each conversation.\n\
````\n\
{messages}\n\
````"""
