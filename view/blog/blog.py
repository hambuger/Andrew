import hashlib
import logging
import os

from flask import request, Blueprint

from database_util.es.es import query_data_by_id_or_parent_id

blog_route = Blueprint('blog', __name__)

logger = logging.getLogger(__name__)


@blog_route.route('/blog/query', methods=['GET'])
def blog():
    id = request.args.get('id')
    parent_id = request.args.get('parentId')
    response = query_data_by_id_or_parent_id(id, parent_id)
    logger.debug(response)
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
    # Generate a unique string using the MD5 hash function
    hash_object = hashlib.md5(image_file.filename.encode())
    hex_dig = hash_object.hexdigest()
    # Use the hash result as the filename
    filename = hex_dig + '.jpg'
    save_path = os.path.join(save_directory, filename)
    image_file.save(save_path)

    # Return a successful upload response, including the saved image path
    image_url = '/picture/' + filename  # Replace with your image access path
    return {'message': 'Image uploaded successfully', 'url': image_url}
