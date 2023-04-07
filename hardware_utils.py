CONVERSION_TABLE = {"left_motor": "left_us",
                    "right_motor": "right_us"}


def convert_values(value: any) -> any:
    if type(value) == str:
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False

    return value
