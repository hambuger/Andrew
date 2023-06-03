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
````{result}````\n Do not reveal in your reply if they are unuseful\nNow is {current_time_str}\n"
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
