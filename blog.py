from elasticsearch import Elasticsearch

es = Elasticsearch(hosts=["http://localhost:9200"])  # assume localhost & default port

# 插入数据
def insert_data(index_name, id, document):
    res = es.index(index=index_name, id=id, body=document)
    return res

# 更新数据
def update_data(index_name, id, document):
    res = es.update(index=index_name, id=id, body={'doc': document})
    return res

# 查询数据
def query_data(index_name, query):
    res = es.search(index=index_name, body=query)
    return res


def query_data_by_id(id, parent_id):
    if id:
        return es.get(index="blog", id=id)
    else:
        query = {
            'query': {
                'bool': {
                    'must': [
                        {'match': {'parent_node_id': parent_id}}
                    ]
                }
            }
        }
        res = es.search(index="blog", body=query)
        return res


# 插入示例
document = {
    'title': 'My Title',
    'content': 'My Content',
    'creation_time': '2023-05-27 12:00:00',
    'modification_time': '2023-05-27 12:00:00',
    'is_deleted': 'false',
    'type': 'My Type',
    'node_id': 1,
    'parent_node_id': 0
}
insert_data('blog',1, document)

# 更新示例
update_document = {'content': 'Updated Content'}
update_data('blog', 1, update_document)

# 查询示例
query = {
    'query': {
        'bool': {
            'should': [
                {'match': {'title': 'My Title'}},
                {'match': {'content': 'My Content'}},
                {'term': {'node_id': 1}}
            ]
        }
    }
}
results = query_data('blog', query)
print(results)
