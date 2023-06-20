import json

from config.global_logger import logger

FUNCTIONS = {}


def register(function_info):
    def decorator(function):
        FUNCTIONS[function.__name__] = {
            'method': function,
            'info': function_info
        }
        return function

    return decorator


@register({
    "name": "get_current_weather",
    "description": "Get the weather conditions for a location",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "place name",
            },
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
        },
        "required": ["location"],
    },
})
def get_current_weather(location, unit="celsius"):
    weather_info = {
        "location": location,
        "temperature": "30",
        "unit": unit,
        "forecast": ["sunny", "windy"],
    }
    return weather_info


@register({
    "name": "get_map_navigation",
    "description": "Get directions to destination",
    "parameters": {
        "type": "object",
        "properties": {
            "destination": {
                "type": "string",
                "description": "destination name"
            }
        },
        "required": ["destination"]
    },
})
def get_map_navigation(args):
    return {
        "destination": args['destination'],
        "way": "如果你在附近城市，可以选择乘坐高铁到达杭州。杭州有多个高铁站，包括杭州东站、杭州站和杭州南站等。到达高铁站后，你可以通过地铁、出租车或公共汽车等方式前往目的地"
    }


@register({
    "name": "call_someone",
    "description": "call someone",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The name of the contact to call"
            }
        },
        "required": ["name"]
    },
})
def call_someone(someone):
    call_result = {
        "success": True,
        "message": "call " + someone['name'] + " success"
    }
    return call_result


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


def invoke_function(function_name, arguments):
    function = FUNCTIONS.get(function_name).get('method')
    if function:
        try:
            return function(json.loads(arguments))
        except json.JSONDecodeError as e:
            logger.error(f"Error while decoding arguments to json: {e}")
            if arguments:
                return function(arguments)
            else:
                return {"error": "Invalid arguments"}
    else:
        return {"error": f"Function {function_name} not found"}
