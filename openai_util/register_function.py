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
    "description": "获取某个地点的天气情况",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "地点名称",
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
    "description": "获取到达目的地路线",
    "parameters": {
        "type": "object",
        "properties": {
            "destination": {
                "type": "string",
                "description": "目的地名称"
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
    "description": "给联系人打电话",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "要拨打的联系人名称"
            }
        },
        "required": ["name"]
    },
})
def call_someone(someone):
    call_result = {
        "success": True,
        "message": "拨打" + someone['name'] + "成功"
    }
    return call_result


def do_step_by_step():
    return {
        "name": "do_step_by_step",
        "description": "按照用户指令一步步执行操作",
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
                                "description": "执行操作的顺序"
                            },
                            "step_method": {
                                "type": "string",
                                "description": "要执行的操作对应的方法名",
                                "enum": list(FUNCTIONS.keys())
                            },
                            "step_desc": {
                                "type": "string",
                                "description": "要执行的操作描述，原子化的操作"
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
            "description": "获取应该调用的方法",
            "parameters": {
                "type": "object",
                "properties": {
                    "function_name": {
                        "type": "string",
                        "description": "应该调用的方法名",
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
