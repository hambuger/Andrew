from openai_util.function_call.funcation_invoke import FUNCTIONS


def register(function_info):
    def decorator(function):
        FUNCTIONS[function.__name__] = {
            'method': function,
            'info': function_info
        }
        return function

    return decorator


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
def get_map_navigation(destination):
    return {
        "destination": destination,
        "way": "如果你在附近城市，可以选择乘坐高铁到达杭州。杭州有多个高铁站，包括杭州东站、杭州站和杭州南站等。到达高铁站后，你可以通过地铁、出租车或公共汽车等方式前往目的地"
    }
