import logging
import os

# 创建 logger
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)  # 设置日志级别为INFO

if not os.path.exists('tmp'):
    os.makedirs('tmp')

# 创建文件处理器并设置级别为INFO
file_handler = logging.FileHandler('tmp/app.log', encoding='utf-8', mode='a')
file_handler.setLevel(logging.DEBUG)

# 创建 formatter
formatter = logging.Formatter('%(asctime)s [File: %(filename)s Line: %(lineno)d]: %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')

# 添加 formatter 到 file_handler
file_handler.setFormatter(formatter)

# 添加 file_handler 到 logger
logger.addHandler(file_handler)
