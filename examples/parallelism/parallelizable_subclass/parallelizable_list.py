from typing import Generic, List

from hamilton.htypes import Parallelizable, ParallelizableElement


class ParallelizableList(
    List[ParallelizableElement], Parallelizable, Generic[ParallelizableElement]
):
    """
    Marks the output of a function node as parallelizable and also as a list.

    It has the same usage as "Parallelizable", but for returns that are specifically
    lists, for correct functioning of linters and other tools.
    """

    pass
