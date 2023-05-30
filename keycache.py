import random
import time
import redis


class ApiKeyManager:
    def __init__(self, redis_host='localhost', redis_port=6379, db=0):
        self.r = redis.Redis(host=redis_host, port=redis_port, db=db)

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

    # 获取可用的key, 指数退避重试，最多重试5次
    def get_key(self, max_retries=5):
        for i in range(max_retries):
            key = self.get_key_script(args=[time.time()])
            if key is not None:
                return key.decode()  # Redis返回的key是bytes，需要decode转为str

            # 指数退避
            backoff_time = 2 ** i + random.uniform(0, 1)
            time.sleep(backoff_time)

        raise Exception("太多请求，没有可用的key了")

    def remove_all_keys(self):
        self.r.delete('api_keys')

    def get_gh_chat_model_key(self):
        return self.r.get('gh_chat_model_key').decode()
