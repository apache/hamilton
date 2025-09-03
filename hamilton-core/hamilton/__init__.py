import importlib.util
import pathlib
import sys
from typing import Any
from types import ModuleType


def _load_hamilton_module() -> ModuleType:
    """Patch this relative import in the Hamilton core repository

    ```python
    # hamilton/__init__.py
    try:
        from .version import VERSION as __version__  # noqa: F401
    except ImportError:
        from version import VERSION as __version__  # noqa: F401
    ```
    """

    origin_path = pathlib.Path(__file__).parent / "_hamilton" / "__init__.py"
    origin_spec = importlib.util.spec_from_file_location("hamilton", origin_path)
    origin_module = importlib.util.module_from_spec(origin_spec)

    # The following lines are only required if we don't modify `hamilton/__init__.py`
    # source_segment = "from version import VERSION as __version__"
    # # the namespace `hamilton._hamilton` is only temporarily available; it will be removed
    # # by the end of this initialization
    # patched_segment = "from hamilton._hamilton.version import VERSION as __version__"

    # source_code = pathlib.Path(origin_path).read_text()
    # patched_code = source_code.replace(source_segment, patched_segment)

    # exec(patched_code, origin_module.__dict__)
    # sys.modules["hamilton"] = origin_module

    origin_spec.loader.exec_module(origin_module)
    return origin_module


def _load_hamilton_registry_module():
    module_path = pathlib.Path(__file__).parent / "_hamilton" / "registry.py"
    module_spec = importlib.util.spec_from_file_location("hamilton.registry", module_path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def _create_proxy_module() -> ModuleType:
    proxy_module = ModuleType(__name__)
    sys.modules[__name__] = proxy_module
    return proxy_module


_registry_module = _load_hamilton_registry_module()
# disable plugin autoloading
_registry_module.disable_autoload()

_origin_module = _load_hamilton_module()
_proxy_module = _create_proxy_module()

def __getattr__(name: str) -> Any:
    try:
        return getattr(_origin_module, name)
    except AttributeError:
        raise AttributeError(f"module {__name__} has no attribute {name}")

# `getattr()` must be available to build the package
_proxy_module.__getattr__ = __getattr__
