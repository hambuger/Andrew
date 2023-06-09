from steamship import Steamship
from openai_util.prompt import get_message_important_score

client = Steamship(workspace="gpt-4")
generator = client.use_plugin('gpt-4', config={"temperature": 0})


def chat_use_stream_ship(content):
    task = generator.generate(
        text=get_message_important_score(content))
    task.wait()
    return task.output.blocks[0].text
