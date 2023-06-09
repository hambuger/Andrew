import openai
from util.redis.redis_client import api_key_manager
import numpy as np


def get_embedding(content):
    openai.api_key = api_key_manager.get_openai_key()
    embedding = openai.Embedding.create(input=[content], model="text-embedding-ada-002")
    return np.array(embedding["data"][0]["embedding"]).tolist()