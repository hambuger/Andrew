import importlib
import os

# 获取当前工作目录
current_directory = os.getcwd()

try:
    # 导入模块
    for filename in os.listdir(os.path.join(current_directory, "learn_skill")):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = "learn_skill." + filename[:-3]
            module = importlib.import_module(module_name)
except Exception as e:
    print(e)
