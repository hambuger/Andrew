from elasticsearch import Elasticsearch, helpers
import os

# init
es = Elasticsearch(hosts=[os.getenv("ES_HOST", "http://localhost:9200")])


# insert
def insert_index_doc(index_name, id, document):
    res = es.index(index=index_name, id=id, body=document)
    return res


# update
def update_index_doc(index_name, id, document):
    res = es.update(index=index_name, id=id, body={'doc': document})
    return res


# query
def query_data(index_name, query):
    res = es.search(index=index_name, body=query)
    return res


def query_data_by_id_or_parent_id(id, parent_id):
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
            },
            'sort': [
                {'creation_time': {'order': 'desc'}}
            ]
        }
        res = es.search(index="blog", body=query)
        return res


def bulk_insert(actions):
    helpers.bulk(es, actions)
