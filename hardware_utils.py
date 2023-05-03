import ast
import re

CONVERSION_TABLE = {}


def convert_values(value: any) -> any:
    if type(value) == str:
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        elif re.match(r"^[-+]?[0-9]+$", value):
            return int(value)

    else:
        return ast.literal_eval(value)

    return value