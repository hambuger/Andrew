from steamship import Steamship, SteamshipError
from util.redis.redis_client import api_key_manager


def get_generator():
    client = Steamship(workspace="gpt-4", api_key=api_key_manager.r.lindex('stream_ship_keys', 0))
    return client.use_plugin('gpt-4', config={"temperature": 0})


generator = get_generator()


def chat_use_stream_ship(content):
    global generator  # 声明 generator 是一个全局变量
    try:
        task = generator.generate(text=content)
        task.wait()
        return task.output.blocks[0].text
    except SteamshipError as e:
        if e.code == 'LimitReached':
            api_key_manager.r.lpop('stream_ship_keys')
            generator = get_generator()  # 更新全局变量 generator
            new_task = generator.generate(text=content)
            new_task.wait()
            return new_task.output.blocks[0].text
        else:
            return 0
