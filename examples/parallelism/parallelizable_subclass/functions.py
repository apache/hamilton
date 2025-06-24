from parallelizable_list import ParallelizableList

from hamilton.htypes import Collect


def hello_list() -> ParallelizableList[str]:
    return ["h", "e", "l", "l", "o", " ", "l", "i", "s", "t"]


def uppercase(hello_list: str) -> str:
    return hello_list.upper()


def hello_uppercase(uppercase: Collect[str]) -> str:
    return "".join(uppercase)
