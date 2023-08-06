import importlib
import os

# Get the current working directory
current_directory = os.getcwd()

try:
    # import module
    for filename in os.listdir(os.path.join(current_directory, "learn_skill")):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = "learn_skill." + filename[:-3]
            module = importlib.import_module(module_name)
except Exception as e:
    print(e)
