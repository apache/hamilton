# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

# code in this module should no depend on much
from typing import Any, Callable, List, Optional, Set, Tuple, Union


def convert_output_value(
    output_value: Union[str, Callable, Any], module_set: Set[str]
) -> Tuple[Optional[str], Optional[str]]:
    """Converts output values that one can request into strings.

    It checks that if it's a function, it's in the passed in module set.

    :param output_value: the value we want to convert into a string. We don't annotate driver.Variable here for
       import reasons.
    :param module_set: the set of modules functions could come from.
    :return: a tuple, (string value, string error). One or the other is returned, never both.
    """
    if isinstance(output_value, str):
        return output_value, None
    elif hasattr(output_value, "name"):
        return output_value.name, None
    elif isinstance(output_value, Callable):
        if output_value.__module__ in module_set:
            return output_value.__name__, None
        else:
            return None, (
                f"Function {output_value.__module__}.{output_value.__name__} is a function not "
                f"in a "
                f"module given to the materializer. Valid choices are {module_set}."
            )
    else:
        return None, (
            f"Materializer dependency {output_value} is not a string, a function, or a driver.Variable."
        )


def convert_output_values(
    output_values: List[Union[str, Callable, Any]], module_set: Set[str]
) -> List[str]:
    """Checks & converts outputs values to strings. This is used in building dependencies for the DAG.

    :param output_values: the values to convert.
    :param module_set: the modules any functions could come from.
    :return: the final values
    :raises ValueError: if there are values that can't be used/converted.
    """
    final_values = []
    errors = []
    for final_var in output_values:
        _val, _error = convert_output_value(final_var, module_set)
        if _val:
            final_values.append(_val)
        if _error:
            errors.append(_error)
    if errors:
        errors.sort()
        error_str = f"{len(errors)} errors encountered:\n  " + "\n  ".join(errors)
        raise ValueError(error_str)
    return final_values
