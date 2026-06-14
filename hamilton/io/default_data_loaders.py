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

import dataclasses
import io
import json
import os
import pathlib
import pickle
import warnings
from collections.abc import Collection
from typing import Any, Optional

from hamilton.io.data_adapters import DataLoader, DataSaver
from hamilton.io.utils import get_file_metadata

# Module-level allowlist for `PickleLoader`. When set (non-None), only the
# listed `(module, qualname)` pairs may be reconstructed during unpickling.
# Set via `set_pickle_loader_allowlist([...])` or by passing `allowlist=...`
# to a `PickleLoader` instance directly. See `PickleLoader` for details.
_PICKLE_LOADER_ALLOWLIST: Optional[frozenset[tuple[str, str]]] = None


def set_pickle_loader_allowlist(
    allowlist: Optional[Collection[tuple[str, str]]],
) -> None:
    """Configure the module-level allowlist applied to every `PickleLoader`.

    Each entry is a ``(module, qualname)`` pair, e.g. ``("pandas.core.frame", "DataFrame")``.
    When the allowlist is configured, the loader uses a restricted unpickler
    that only reconstructs objects whose ``(module, qualname)`` pair is in
    the allowlist. Anything else raises ``pickle.UnpicklingError``.

    Pass ``None`` to clear the allowlist and restore the unrestricted (and
    noisy: a warning is emitted on each load) default behavior.

    Per-instance allowlists passed to ``PickleLoader(allowlist=...)`` take
    precedence over the module-level value.
    """
    global _PICKLE_LOADER_ALLOWLIST
    if allowlist is None:
        _PICKLE_LOADER_ALLOWLIST = None
    else:
        _PICKLE_LOADER_ALLOWLIST = frozenset((str(m), str(n)) for m, n in allowlist)


class _RestrictedUnpickler(pickle.Unpickler):
    """`pickle.Unpickler` subclass that rejects classes outside an allowlist.

    The standard library's ``pickle`` module permits arbitrary callables to
    be invoked at load time via the ``REDUCE`` opcode (the ``__reduce__``
    protocol). That makes a raw ``pickle.load`` on caller-supplied bytes a
    code-execution primitive. This subclass overrides ``find_class`` to
    consult an allowlist before resolving a global reference, so payloads
    that try to import e.g. ``os.system`` are rejected before any side
    effects occur.
    """

    def __init__(
        self,
        file,
        allowlist: frozenset[tuple[str, str]],
    ) -> None:
        super().__init__(file)
        self._allowlist = allowlist

    def find_class(self, module: str, name: str) -> Any:  # type: ignore[override]
        if (module, name) in self._allowlist:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(
            f"Refusing to load disallowed global '{module}.{name}'. "
            "Add it to the allowlist passed to `PickleLoader(allowlist=...)` "
            "or via `set_pickle_loader_allowlist(...)` if it is trusted."
        )


@dataclasses.dataclass
class JSONDataLoader(DataLoader):
    path: str

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [dict, list]

    def load_data(self, type_: type) -> tuple[dict, dict[str, Any]]:
        with open(self.path, "r") as f:
            return json.load(f), get_file_metadata(self.path)

    @classmethod
    def name(cls) -> str:
        return "json"


@dataclasses.dataclass
class JSONDataSaver(DataSaver):
    path: str

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [dict, list]

    @classmethod
    def name(cls) -> str:
        return "json"

    def save_data(self, data: Any) -> dict[str, Any]:
        with open(self.path, "w") as f:
            json.dump(data, f)
        return get_file_metadata(self.path)


@dataclasses.dataclass
class RawFileDataLoader(DataLoader):
    path: str
    encoding: str = "utf-8"

    def load_data(self, type_: type) -> tuple[str, dict[str, Any]]:
        with open(self.path, "r", encoding=self.encoding) as f:
            return f.read(), get_file_metadata(self.path)

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [str]

    @classmethod
    def name(cls) -> str:
        return "file"


@dataclasses.dataclass
class RawFileDataSaver(DataSaver):
    path: str
    encoding: str = "utf-8"

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [str]

    @classmethod
    def name(cls) -> str:
        return "file"

    def save_data(self, data: Any) -> dict[str, Any]:
        with open(self.path, "w", encoding=self.encoding) as f:
            f.write(data)
        return get_file_metadata(self.path)


@dataclasses.dataclass
class RawFileDataSaverBytes(DataSaver):
    path: pathlib.Path | str

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [bytes, io.BytesIO]

    @classmethod
    def name(cls) -> str:
        return "file"

    def save_data(self, data: bytes | io.BytesIO) -> dict[str, Any]:
        if isinstance(data, io.BytesIO):
            data_bytes = data.getvalue()  # Extract bytes from BytesIO
        else:
            data_bytes = data

        with open(self.path, "wb") as file:
            file.write(data_bytes)

        return get_file_metadata(str(self.path))


@dataclasses.dataclass
class PickleLoader(DataLoader):
    """Loads a Python object from a pickle file.

    Python's ``pickle`` module is not safe to use on data from untrusted
    sources -- a maliciously crafted pickle can execute arbitrary code at
    load time via the ``__reduce__`` protocol. Hamilton's default has
    historically been to call ``pickle.load`` unrestricted, which mirrors
    ``pandas.read_pickle`` and ``joblib.load`` and assumes the caller wrote
    (or otherwise trusts) the file. That assumption is brittle once pickle
    files are shared across teams, downloaded as artifacts, or produced
    upstream by a system the loader does not control.

    To opt into a safer mode, pass ``allowlist`` to this loader or call
    :func:`set_pickle_loader_allowlist` to set a process-wide allowlist.
    Each entry is a ``(module, qualname)`` pair; the loader will only
    reconstruct objects whose qualified name appears in the allowlist and
    will raise ``pickle.UnpicklingError`` otherwise. When no allowlist is
    configured, the loader still loads the file (for backward compatibility)
    but emits a warning to signal that the deserialization is unrestricted.

    :param path: Filesystem path of the pickle file to load.
    :param allowlist: Optional collection of ``(module, qualname)`` pairs
        permitted during unpickling. If ``None`` (the default), falls back
        to the module-level allowlist configured via
        :func:`set_pickle_loader_allowlist`; if that is also ``None``, the
        load is unrestricted and emits a warning.
    """

    path: str
    allowlist: Optional[Collection[tuple[str, str]]] = None

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [object, Any]

    @classmethod
    def name(cls) -> str:
        return "pickle"

    def _resolve_allowlist(self) -> Optional[frozenset[tuple[str, str]]]:
        if self.allowlist is not None:
            return frozenset((str(m), str(n)) for m, n in self.allowlist)
        return _PICKLE_LOADER_ALLOWLIST

    def load_data(self, type_: type[object]) -> tuple[object, dict[str, Any]]:
        allowlist = self._resolve_allowlist()
        with open(self.path, "rb") as f:
            if allowlist is None:
                warnings.warn(
                    "PickleLoader is loading without an allowlist; pickle "
                    "deserialization can execute arbitrary code if the file "
                    "is not fully trusted. Configure an allowlist via "
                    "`PickleLoader(allowlist=...)` or "
                    "`hamilton.io.default_data_loaders.set_pickle_loader_allowlist(...)`.",
                    stacklevel=2,
                )
                obj = pickle.load(f)
            else:
                obj = _RestrictedUnpickler(f, allowlist).load()
            return obj, get_file_metadata(self.path)


@dataclasses.dataclass
class PickleSaver(DataSaver):
    path: str

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [object]

    @classmethod
    def name(cls) -> str:
        return "pickle"

    def save_data(self, data: Any) -> dict[str, Any]:
        with open(self.path, "wb") as f:
            pickle.dump(data, f)
        return get_file_metadata(self.path)


@dataclasses.dataclass
class EnvVarDataLoader(DataLoader):
    names: tuple[str, ...]

    def load_data(self, type_: type[dict]) -> tuple[dict, dict[str, Any]]:
        return {name: os.environ[name] for name in self.names}, {}

    @classmethod
    def name(cls) -> str:
        return "environment"

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [dict]


@dataclasses.dataclass
class LiteralValueDataLoader(DataLoader):
    value: Any

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [Any]

    def load_data(self, type_: type) -> tuple[dict, dict[str, Any]]:
        return self.value, {}

    @classmethod
    def name(cls) -> str:
        return "literal"


@dataclasses.dataclass
class InMemoryResult(DataSaver):
    """Class specifically to returning an in memory result without saving it anywhere.

    Use this to get the result of a combiner easily; depends on their use.
    """

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [Any]

    def save_data(self, data: Any) -> Any:
        return data

    @classmethod
    def name(cls) -> str:
        return "memory"


DATA_ADAPTERS = [
    JSONDataSaver,
    JSONDataLoader,
    LiteralValueDataLoader,
    RawFileDataLoader,
    RawFileDataSaver,
    RawFileDataSaverBytes,
    PickleLoader,
    PickleSaver,
    EnvVarDataLoader,
    InMemoryResult,
]
