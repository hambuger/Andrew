import os
import requests
from openai_util.function_call.openaifunc_decorator import openai_func


@openai_func
def download_file(url: str, save_filename: str):
    """
    download file from a url and save it to a file
    :param url: the url of the file
    :param save_filename: the filename to save
    """
    # 确保tmp文件夹存在
    if not os.path.exists('tmp'):
        os.makedirs('tmp')

    # 在tmp文件夹下保存文件
    local_filename = os.path.join('tmp', save_filename)

    # 发送一个HTTP请求到URL
    response = requests.get(url, stream=True)

    # 确保请求成功
    response.raise_for_status()

    # 打开文件以便写入
    with open(local_filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            # 如果有chunk则写入文件
            if chunk:
                f.write(chunk)

    return os.path.abspath(local_filename)

# print(download_file(
#     'https://ask.qcloudimg.com/http-save/yehe-6781431/fc477e39f845d3a223e42da74bbf645a.png?imageView2/2/w/1200',
#     'demo.jpg'))
