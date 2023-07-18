import requests
import json
from openai_util.function_call.openaifunc_decorator import openai_func


@openai_func
def get_location_by_ip():
    """
    get location by ip
    """
    try:
        response = requests.get('http://ip-api.com/json/')
        data = json.loads(response.text)
        # latitude = data['lat']
        # longitude = data['lon']
        return data['city'] + ', ' + data['regionName'] + ', ' + data['country']
    except requests.exceptions.RequestException as e:
        print('Error:', e)
        return 'Error'

# print(get_location_by_ip())
