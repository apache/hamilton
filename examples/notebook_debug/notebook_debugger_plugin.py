import inspect
import logging
from typing import Any, Callable, Dict, Optional

from hamilton import lifecycle

try:
    import cloudpickle as pickle
except ImportError:
    import pickle

logger = logging.getLogger(__name__)


template = """
try:
    import cloudpickle as pickle
except ImportError:
    import pickle

import {module_name}  # we load this for imports

# let's load the inputs
with open('{node_name}_inputs.pkl', 'rb') as f:
    inputs = pickle.load(f)

# the function that errored
{function_to_debug}


# run the function
{func_name}(**inputs)
"""


class NotebookErrorDebugger(lifecycle.NodeExecutionHook):

    def run_before_node_execution(
        self,
        *,
        node_name: str,
        node_tags: Dict[str, Any],
        node_kwargs: Dict[str, Any],
        node_return_type: type,
        task_id: Optional[str],
        run_id: str,
        node_input_types: Dict[str, Any],
        **future_kwargs: Any,
    ):
        pass

    def run_after_node_execution(
        self,
        *,
        node_name: str,
        node_tags: Dict[str, Any],
        node_kwargs: Dict[str, Any],
        node_return_type: type,
        result: Any,
        error: Optional[Exception],
        success: bool,
        task_id: Optional[str],
        run_id: str,
        originating_function: Callable,
        **future_kwargs: Any,
    ):
        """
        This function will create the follow in the case of a failure:

        1. It will pickle of the inputs to the function.
        2. It will create a file with the following:
            a. it will import the module the function is from -- to cover any imports that need to exist.
            b. it will load the pickled inputs.
            c. it will have the code of the function that errored so you can debug it.
            d. it will then also list python version, hamilton version, and any other relevant package versions for
            the user to install / have.
        2. It will then print out where this data has been saved for the user to then debug.
        """
        if not success:
            # pickle the inputs
            with open(f"{node_name}_inputs.pkl", "wb") as f:
                pickle.dump(node_kwargs, f)
            # create a file with the function and the inputs
            with open(f"{node_name}_debug.py", "w") as f:
                f.write(
                    template.format(
                        module_name=node_tags.get("module"),
                        node_name=node_name,
                        function_to_debug=inspect.getsource(originating_function),
                        func_name=originating_function.__name__,
                    )
                )
            # print out where the data has been saved
            message = (
                f"Inputs to {node_name} have been saved to {node_name}_inputs.pkl\n"
                f"The function that errored has been saved to {node_name}_debug.py\n"
                f"Please run the function in {node_name}_debug.py to debug the error."
            )
            logger.warning(message)
            # TODO: create file with python requirements for pickle to work...
