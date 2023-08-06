import os
import random
import time
import redis


class ApiKeyManager:
    def __init__(self, redis_host=os.getenv("REDIS_HOST"), redis_port=os.getenv("REDIS_PORT", "6379"), db=0):
        self.r = redis.Redis(host=redis_host, port=int(redis_port), db=db)

        self.lua = """
        local keys = redis.call('LRANGE', 'api_keys', 0, -1)
        local now = tonumber(ARGV[1])
        for i, key in ipairs(keys) do
            local usage = redis.call('LRANGE', 'api_key_usage:' .. key, 0, -1)
            local count = 0
            for j, timestamp in ipairs(usage) do
                if now - tonumber(timestamp) < 60 then
                    count = count + 1
                end
            end
            if count < 3 then
                redis.call('LPUSH', 'api_key_usage:' .. key, now)
                redis.call('LTRIM', 'api_key_usage:' .. key, 0, 2)
                return key
            end
        end
        return nil
        """
        self.get_key_script = self.r.register_script(self.lua)

        self.lua2 = """
        local keys = redis.call('LRANGE', 'stream_ship_keys', 0, -1)
        for i, key in ipairs(keys) do
            local total_usage = redis.call('GET', 'stream_ship_key_total_usage:' .. key)
            if total_usage then
                total_usage = tonumber(total_usage)
            else
                total_usage = 0
            end
            if total_usage < 500 then
                redis.call('INCR', 'stream_ship_key_total_usage:' .. key)
                return key
            else
                -- Remove the key from the list if its total usage exceeds 500
                redis.call('LREM', 'stream_ship_keys', 0, key)
            end
        end
        return nil
        """
        self.get_stream_ship_key_script = self.r.register_script(self.lua2)

    # Get available keys, exponential backoff retry, up to 3 retries
    def get_openai_key(self, max_retries=3):
        if os.getenv('IGNORE_KEY_LIMIT') == 'True':
            return self.r.lrange('api_keys', 0, 0)[0].decode()
        else:
            for i in range(max_retries):
                key = self.get_key_script(args=[time.time()])
                if key is not None:
                    return key.decode()  # The key returned by Redis is bytes, which needs to be decoded into str

                # exponential backoff retry
                backoff_time = 2 ** i + random.uniform(0, 1)
                time.sleep(backoff_time)

            raise Exception("Too many requests, no keys available")

    def get_stream_key_key(self, max_retries=3):
        for i in range(max_retries):
            key = self.get_stream_ship_key_script()
            if key is not None:
                return key.decode()  # The key returned by Redis is bytes, which needs to be decoded into str

            # 指数退避
            backoff_time = 2 ** i + random.uniform(0, 1)
            time.sleep(backoff_time)

        raise Exception("Too many requests, no keys available")

    def remove_all_openai_keys(self):
        self.r.delete('api_keys')

    def remove_all_stream_ship_keys(self):
        self.r.delete('stream_ship_keys')

    def get_gh_chat_model_key(self):
        return self.r.get('gh_chat_model_key').decode()

    def update_key_value(self, key, value):
        self.r.set(key, value)

    def get_key_value(self, key):
        value = self.r.get(key)
        if value is None:
            return None
        return value.decode()

    def set_nx_key(self, key, value, lock_timeout_ms=60 * 1000):
        return self.r.set(key, value, nx=True, px=lock_timeout_ms)

    def delete_key(self, key):
        self.r.delete(key)


api_key_manager = ApiKeyManager()
