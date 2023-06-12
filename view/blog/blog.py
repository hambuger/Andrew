import hashlib
import logging
import os

from flask import request, Blueprint

from util.es.es import query_data_by_id_or_parent_id

blog_route = Blueprint('blog', __name__)

logger = logging.getLogger(__name__)


@blog_route.route('/blog/query', methods=['GET'])
def blog():
    id = request.args.get('id')
    parent_id = request.args.get('parentId')
    response = query_data_by_id_or_parent_id(id, parent_id)
    logger.info(response)
    if not response:
        return None
    if id:
        if response['_source']:
            title = response['_source'].get('title', '')
            content = response['_source'].get('content', '')
            node_id = response['_source'].get('node_id', '')
            type = response['_source'].get('type', '')
            return {"title": title, "content": content, "id": node_id, "type": type}
        else:
            return None
    result = []
    if response and response['hits']['total']['value'] == 0:
        return result
    for index, hit in enumerate(response['hits']['hits']):
        title = hit['_source'].get('title', '')
        content = hit['_source'].get('content', '')
        node_id = hit['_source'].get('node_id', '')
        type = hit['_source'].get('type', '')
        result.append({"title": title, "content": content, "id": node_id, "type": type})
    return result


@blog_route.route('/upload/image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return 'No image file found', 400

    image_file = request.files['image']
    if image_file.filename == '':
        return 'Invalid image file', 400
    save_directory = '/var/www/picture'
    # 使用 MD5 哈希函数生成唯一的字符串
    hash_object = hashlib.md5(image_file.filename.encode())
    hex_dig = hash_object.hexdigest()
    # 将哈希结果作为文件名
    filename = hex_dig + '.jpg'
    save_path = os.path.join(save_directory, filename)
    image_file.save(save_path)

    # 返回上传成功的响应，包含保存的图片路径
    image_url = '/picture/' + filename  # 替换为你的图片访问路径
    return {'message': 'Image uploaded successfully', 'url': image_url}
