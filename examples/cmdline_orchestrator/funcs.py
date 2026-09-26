import time
from subprocess import CompletedProcess

from cmdline import cmdline_decorator

from hamilton.function_modifiers import tag


@tag(cache="pickle")
@cmdline_decorator
def echo_1(start: str) -> str:
    time.sleep(2)
    return f'echo "1: {start}"'


@tag(cache="pickle")
@cmdline_decorator
def echo_2(echo_1: str) -> str:
    time.sleep(2)
    return f'echo "2: {echo_1}"'


@tag(cache="pickle")
@cmdline_decorator
def echo_2b(echo_1: str) -> [str, CompletedProcess, str]:
    # preprocess
    print("preprocess")
    time.sleep(2)
    msg = f'echo "2b: {echo_1}"'
    completed_process = yield msg
    # postprocess
    print("postprocess")
    time.sleep(2)
    output = completed_process.stdout + "!!!"
    return output


@tag(cache="pickle")
@cmdline_decorator
def echo_3(echo_2: str, echo_2b: str) -> str:
    return f'echo "3: {echo_2 + ":::" + echo_2b}"'
