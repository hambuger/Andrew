import tiktoken
import os

gpt_3_encoding = tiktoken.encoding_for_model(os.getenv("ENCODING_FOR_MODEL", "gpt-3.5-turbo"))


def get_content_token_len(content):
    return len(gpt_3_encoding.encode(content))


def sum_text_token(text_list):
    tokens = 0
    for text in text_list:
        tokens = tokens + len(gpt_3_encoding.encode(text))
    return tokens
