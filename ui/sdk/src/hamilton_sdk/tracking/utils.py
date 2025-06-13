import dataclasses
import datetime
import json
import logging
from enum import Enum
from typing import Any, Union

import numpy as np

logger = logging.getLogger(__name__)


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            # Attempt to serialize the object using the default method
            return json.JSONEncoder.default(self, obj)
        except TypeError as e:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Failed to serialize object of type {type(obj)}: {e}")
            # If not serializable, convert to string
            str_object = str(obj)
            if len(str_object) > 500:
                return str_object[:200] + "..."
            return str_object


def make_json_safe(item: Union[dict, list, str, float, int, bool]) -> Any:
    """
    Converts an item to json-serializable format, converting datetime objects to string.

    @param item: A dictionary or list potentially containing non-serializable types.
    @return: A dictionary or list with non-serializable types converted.
    """
    if isinstance(item, dict):
        return {k: make_json_safe(v) for k, v in item.items()}
    elif isinstance(item, list):
        return [make_json_safe(elem) for elem in item]
    elif isinstance(item, np.ndarray):
        return make_json_safe(list(item))
    elif isinstance(item, datetime.datetime):
        return item.isoformat()  # Convert datetime object to iso format string
    elif dataclasses.is_dataclass(item):
        return make_json_safe(dataclasses.asdict(item))
    elif isinstance(item, Enum):
        return item.value  # Convert enum to its corresponding value
    elif hasattr(item, "to_json"):
        # we convert to json string and then deserialize it so that
        # it's not a string in the UI.
        try:
            if hasattr(item, "head"):
                item = item.head()  # truncate to head rows if it's a dataframe
            return json.loads(item.to_json())
        except Exception:
            # pass
            return str(item)[0:200] + "..."
    elif hasattr(item, "to_dict"):
        return make_json_safe(item.to_dict())
    else:
        try:
            json.dumps(item, allow_nan=False)  # Check if item is json serializable
            if isinstance(item, str):
                # escape null byte -- postgres doesn't like null bytes at least.
                # we might need to escape more things; TBD.
                return item.replace("\x00", "\\x00")
            return item
        except (TypeError, ValueError):
            return str(item)  # Convert item to string if not json serializable
