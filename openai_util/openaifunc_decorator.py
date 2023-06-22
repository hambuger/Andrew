import inspect
import functools
import importlib.util
import re
from openai_functions import FUNCTIONS

# Map python types to JSON schema types
type_mapping = {
    "int": "integer",
    "float": "number",
    "str": "string",
    "bool": "boolean",
    "list": "array",
    "tuple": "array",
    "dict": "object",
    "None": "null",
}


def get_type_mapping(param_type):
    param_type = param_type.replace("<class '", '')
    param_type = param_type.replace("'>", '')
    return type_mapping.get(param_type, "string")


def get_description(docstring):
    lines = docstring.split('\n')

    # Find the index of the first line that starts with ':param'
    param_idx = next((idx for idx, line in enumerate(lines) if line.strip().startswith(':param')), len(lines))

    # The method description is the first part of the docstring, and the parameter descriptions are the rest
    method_description = '\n'.join(lines[:param_idx]).strip()

    param_descriptions = {}
    if docstring:
        # Look for lines like ":param param_name: description"
        pattern = re.compile(r':param (\w+): (.+)')
        matches = pattern.findall(docstring)

        for param_name, description in matches:
            param_descriptions[param_name] = description

    return method_description, param_descriptions


def get_params_dict(params, param_descriptions):
    params_dict = {}
    required_params = []
    # Add optional pydantic support
    pydantic_found = importlib.util.find_spec("pydantic")
    if pydantic_found:
        from pydantic import BaseModel
    for k, v in params.items():
        try:
            if pydantic_found and inspect.isclass(v.annotation) and issubclass(v.annotation, BaseModel):
                # Consider BaseModel fields as dictionaries
                params_dict[k] = {
                    "type": "object",
                    "properties": {
                        field_name: {
                            "type": property.get("type", "unknown"),
                            "description": property.get("description") or param_descriptions.get(field_name) or '',
                        }
                        for field_name, property in v.annotation.schema()["properties"].items()
                    },
                }
                # Determine whether the field is required based on whether it has a default value
                params_dict[k]["required"] = [
                    field_name for field_name, field in v.annotation.__fields__.items()
                    if field.default == inspect.Parameter.empty
                ]
                # Determine whether the parameter itself is required
                if v.default == inspect.Parameter.empty:
                    required_params.append(k)
                continue
        except TypeError:
            pass
        annotation = str(v.annotation).split("[")

        try:
            param_type = annotation[0]
        except IndexError:
            param_type = "string"

        try:
            array_type = annotation[1].strip("]")
        except IndexError:
            array_type = "string"

        param_type = get_type_mapping(param_type)
        params_dict[k] = {
            "type": param_type,
            "description": param_descriptions.get(k, ''),
        }
        # Check if the parameter has a default value
        if v.default == inspect.Parameter.empty:
            required_params.append(k)

        if param_type == "array":
            if "," in array_type:
                array_types = array_type.split(", ")
                params_dict[k]["prefixItems"] = []
                for i, array_type in enumerate(array_types):
                    array_type = get_type_mapping(array_type)
                    params_dict[k]["prefixItems"].append({
                        "type": array_type,
                    })
            else:
                array_type = get_type_mapping(array_type)
                params_dict[k]["items"] = {
                    "type": array_type,
                }

    return params_dict, required_params


def openai_func(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    # Get information about function parameters
    params = inspect.signature(func).parameters
    method_description, param_descriptions = get_description(inspect.getdoc(func) or "")
    params_dict, required_params = get_params_dict(params, param_descriptions)
    FUNCTIONS[func.__name__] = {
        'method': func,
        'info': {
            "name": func.__name__,
            "description": method_description,
            "parameters": {
                "type": "object",
                "properties": params_dict,
                "required": required_params,
            },
        }
    }

    return wrapper
