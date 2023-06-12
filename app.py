import os
from dotenv import load_dotenv
from flask import Flask
from openai_util.chat import chat_route
from view.blog.blog import blog_route
from view.chat.my_chat import my_chat_route
from view.excel.excel import excel_route

# 创建一个flask应用
app = Flask(__name__)
# 加载配置文件
load_dotenv()
# 导入并注册路由
app.register_blueprint(excel_route)
app.register_blueprint(blog_route)
app.register_blueprint(chat_route)
app.register_blueprint(my_chat_route)
# 设置一个密钥，用于保存session
app.secret_key = os.getenv('APP_SECRET_KEY')
