import json
from config.global_logger import logger

FUNCTIONS = {}


def invoke_function(function_name, arguments):
    function = FUNCTIONS.get(function_name).get('method')
    if function:
        try:
            return function(**json.loads(arguments))
        except BaseException as e:
            logger.error(f"Error while decoding arguments to json: {e}, arguments:{arguments}")
            if arguments:
                return function(arguments)
            else:
                return {"error": "Invalid arguments"}
    else:
        return {"error": f"Function {function_name} not found"}


def get_invoke_method_info(function_args):
    return get_invoke_method_info_by_name(function_args["function_name"])


def get_invoke_method_info_by_name(function_name):
    if function_name == 'get_invoke_method_info':
        all_method_info = {
            "name": "get_invoke_method_info",
            "description": "Get the method that should be called",
            "parameters": {
                "type": "object",
                "properties": {
                    "function_name": {
                        "type": "string",
                        "description": "The method name that should be called",
                    },
                    "unit": {"type": "string", "enum": list(FUNCTIONS.keys())},
                },
                "required": ["function_name"],
            },
        }
        if not FUNCTIONS.get(function_name):
            FUNCTIONS['get_invoke_method_info'] = {
                'method': get_invoke_method_info,
                'info': all_method_info
            }
        return all_method_info
    else:
        return FUNCTIONS.get(function_name).get('info')


def do_step_by_step():
    return {
        "name": "do_step_by_step",
        "description": "Perform operations step by step according to user instructions",
        "parameters": {
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "step_order": {
                                "type": "integer",
                                "description": "The order in which operations are performed"
                            },
                            "step_method": {
                                "type": "string",
                                "description": "The method name corresponding to the operation to be performed",
                                "enum": list(FUNCTIONS.keys())
                            },
                            "step_desc": {
                                "type": "string",
                                "description": "Description of the operation to be performed, atomic operation"
                            }
                        },
                        "required": ["step_order", "step_method", "step_desc"]
                    }
                }
            },
            "required": ["steps"]
        }
    }


def get_function_result_from_openai_response(response):
    message = response.choices[0].message
    if not message.get("function_call"):
        if not message.get('content'):
            return None, message.get('content')
        else:
            return None, None
    else:
        message.get("function_call")
        function_name = message["function_call"]["name"]
        function_args = message["function_call"]["arguments"]
        logger.debug("invoke method：" + function_name + " args：" + str(function_args))
        return function_name, invoke_function(function_name, function_args)
