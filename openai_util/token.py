import tiktoken
import os

gpt_3_encoding = tiktoken.encoding_for_model(os.getenv("ENCODING_FOR_MODEL", "gpt-3.5-turbo"))


def get_content_token_len(content):
    return len(gpt_3_encoding.encode(content))
