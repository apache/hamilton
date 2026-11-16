import functools
import subprocess

from hamilton.execution.executors import DefaultExecutionManager, TaskExecutor
from hamilton.execution.grouping import TaskImplementation
from hamilton.function_modifiers import tag


class CMDLineExecutionManager(DefaultExecutionManager):
    def get_executor_for_task(self, task: TaskImplementation) -> TaskExecutor:
        """Simple implementation that returns the local executor for single task executions,

        :param task: Task to get executor for
        :return: A local task if this is a "single-node" task, a remote task otherwise
        """
        is_single_node_task = len(task.nodes) == 1
        if not is_single_node_task:
            raise ValueError("Only single node tasks supported")
        (node,) = task.nodes
        if "cmdline" in node.tags:  # hard coded for now
            return self.remote_executor
        return self.local_executor


import inspect


def cmdline_decorator(func):
    """Decorator to run the result of a function as a command line command."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if inspect.isgeneratorfunction(func):
            # If the function is a generator, then we need to run it and capture the output
            # in order to return it
            gen = func(*args, **kwargs)
            cmd = next(gen)
            # Run the command and capture the output
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            try:
                gen.send(result)
                raise ValueError("Generator cannot have multiple yields.")
            except StopIteration as e:
                return e.value
        else:
            # Get the command from the function
            cmd = func(*args, **kwargs)

            # Run the command and capture the output
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            # Return the output
            return result.stdout

    if inspect.isgeneratorfunction(func):
        # get the return type and set it as the return type of the wrapper
        wrapper.__annotations__["return"] = inspect.signature(func).return_annotation[2]
    wrapper = tag(cmdline="yes")(wrapper)
    return wrapper
