import sys
from io import StringIO
from openai_util.function_call.openaifunc_decorator import openai_func


@openai_func
def run_python_code(command: str, _globals=None, _locals=None) -> str:
    """
    Run Python code and returns anything printed to stdout.

    :param command: The Python code to be executed.
    :param _globals : A dictionary representing the global namespace for the executed code. If not provided, an empty dictionary will be used.
    :param _local : A dictionary representing the local namespace for the executed code. If not provided, an empty dictionary will be used.
    """

    # If globals or locals dictionaries are not provided, initialize them.
    if _globals is None:
        _globals = {}
    if _locals is None:
        _locals = {}

    # Save the original sys.stdout value
    old_stdout = sys.stdout

    # Redirect sys.stdout to a StringIO object
    sys.stdout = mystdout = StringIO()

    try:
        # Execute the command
        exec(command, _globals, _locals)

        # Reset sys.stdout to its original value
        sys.stdout = old_stdout

        # Get the output from the StringIO object
        output = mystdout.getvalue()
    except Exception as e:
        # If there's an error, reset sys.stdout and return the error
        sys.stdout = old_stdout
        output = repr(e)
    return output

# code = """
# a = 10
# b = 20
# print(a + b)
# """
# print(run_python_code(code))
