def input_function() -> int:
    return 2


def output_function(input_function: int) -> int:
    return input_function + 1


def error_function(input_function: int, output_function: int, input: int) -> int:
    raise ValueError("This is an error")
    return input_function + output_function + input
