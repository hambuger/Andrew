import logging
import os

# create logger
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)  # Set the log level to INFO

if not os.path.exists('tmp'):
    os.makedirs('tmp')

# Create a file handler and set the level to INFO
file_handler = logging.FileHandler('tmp/app.log', encoding='utf-8', mode='a')
file_handler.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s [File: %(filename)s Line: %(lineno)d]: %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')

# add formatter to file_handler
file_handler.setFormatter(formatter)

# add file_handler to logger
logger.addHandler(file_handler)
