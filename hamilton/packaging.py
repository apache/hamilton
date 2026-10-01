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

"""Subgraph packaging for Hamilton dataflows.

This module lets you carve a group of nodes out of a built dataflow and treat it as a
first-class, reusable unit: a :class:`NodePackage`. A package records the nodes it
provides (with their output types), the external dependencies it requires (with the
types it expects), the configuration keys it needs, and the dependency edges among all
of these. Packages can be serialized to a JSON manifest, exported to and imported from
files, validated for compatibility against a host dataflow's graph, checked for
conflicts against other packages, and composed into larger packages.
"""

import heapq
import json
import pathlib
import typing
from collections.abc import Iterable, Mapping
from typing import Any

from hamilton import graph, htypes
from hamilton.node import DependencyType

VALIDATION_CATEGORIES = frozenset(
    {
        "version_too_low",
        "node_collision",
        "dependency_type_mismatch",
        "missing_dependency",
        "config_requirement_missing",
    }
)

CONFLICT_CATEGORIES = frozenset(
    {
        "duplicate_node",
        "requirement_mismatch",
        "requirement_disagreement",
    }
)

MANIFEST_FIELDS = ("name", "version", "provides", "requires", "dependencies", "config_keys")


class PackagingError(Exception):
    """Base exception for the packaging module.

    Raised when a package, manifest, or helper is constructed or called with
    invalid arguments.
    """


class PackageValidationError(PackagingError):
    """Raised when a package fails validation against a host graph.

    Carries the full :class:`ValidationReport` as the ``report`` attribute; the
    exception message contains the message of every problem in the report.
    """

    def __init__(self, report: "ValidationReport"):
        """Creates the error from a failed validation report.

        :param report: The report describing why validation failed.
        """
        if not isinstance(report, ValidationReport):
            raise PackagingError(
                f"PackageValidationError expects a ValidationReport, got {type(report)}."
            )
        if report.is_valid:
            raise PackagingError(
                "PackageValidationError requires a report with at least one problem."
            )
        self.report = report
        message_lines = [
            f"Package '{report.package_name}' failed validation against the host graph:"
        ]
        for problem in report.problems:
            message_lines.append(f"  [{problem.category}] {problem.message}")
        super().__init__("\n".join(message_lines))


class PackageConflictError(PackagingError):
    """Raised when packages being composed conflict with each other.

    Carries every detected :class:`PackageConflict` as the ``conflicts`` attribute;
    the exception message contains the message of every conflict.
    """

    def __init__(self, conflicts: Iterable["PackageConflict"]):
        """Creates the error from the detected conflicts.

        :param conflicts: The conflicts that prevented composition.
        """
        materialized = list(conflicts)
        for conflict in materialized:
            if not isinstance(conflict, PackageConflict):
                raise PackagingError(
                    f"PackageConflictError expects PackageConflict instances, got {type(conflict)}."
                )
        if not materialized:
            raise PackagingError("PackageConflictError requires at least one conflict.")
        self.conflicts = tuple(materialized)
        message_lines = ["Package composition failed due to conflicts:"]
        for conflict in self.conflicts:
            message_lines.append(f"  [{conflict.category}] {conflict.message}")
        super().__init__("\n".join(message_lines))


def _validate_string(value: Any, description: str) -> str:
    """Validates that a value is a non-empty string.

    :param value: Value to check.
    :param description: Human-readable description used in the error message.
    :return: The validated string.
    """
    if not isinstance(value, str):
        raise PackagingError(f"{description} must be a string, got {type(value)}.")
    if not value:
        raise PackagingError(f"{description} must be a non-empty string.")
    return value


def _validate_version(value: Any, description: str) -> int:
    """Validates that a value is an integer version of at least 1.

    :param value: Value to check.
    :param description: Human-readable description used in the error message.
    :return: The validated version.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise PackagingError(f"{description} must be an integer, got {type(value)}.")
    if value < 1:
        raise PackagingError(f"{description} must be at least 1, got {value}.")
    return value


def _is_type_annotation(value: Any) -> bool:
    """Tells whether a value is usable as a type annotation for a package boundary.

    :param value: Value to check.
    :return: True if the value is a type, a generic alias, or ``typing.Any``.
    """
    return value is Any or isinstance(value, type) or typing.get_origin(value) is not None


def _validate_type_mapping(value: Any, description: str) -> dict[str, Any]:
    """Validates a name-to-type mapping and returns it sorted by name.

    :param value: Mapping to check. None is treated as empty.
    :param description: Human-readable description used in the error messages.
    :return: A new dict sorted by key.
    """
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise PackagingError(
            f"{description} must be a mapping of names to types, got {type(value)}."
        )
    for key, type_ in value.items():
        _validate_string(key, f"{description} name {key!r}")
        if not _is_type_annotation(type_):
            raise PackagingError(f"{description} entry '{key}' must map to a type, got {type_!r}.")
    return {key: value[key] for key in sorted(value)}


def _validate_names(value: Any, description: str) -> tuple[str, ...]:
    """Validates an iterable of names and returns them deduplicated and sorted.

    :param value: Iterable of names to check. None is treated as empty.
    :param description: Human-readable description used in the error messages.
    :return: A sorted tuple of unique names.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, Iterable):
        raise PackagingError(f"{description} must be an iterable of strings, got {type(value)}.")
    materialized = list(value)
    for name in materialized:
        _validate_string(name, f"{description} entry {name!r}")
    return tuple(sorted(set(materialized)))


def _validate_dependency_edges(
    owner: str,
    provides: Mapping[str, Any],
    known_targets: set[str],
    dependencies: Any,
) -> dict[str, tuple[str, ...]]:
    """Validates dependency edges and returns them normalized.

    :param owner: Label of the owning package or manifest, used in error messages.
    :param provides: The provided-name mapping edges may be declared for.
    :param known_targets: Every name an edge may point at.
    :param dependencies: Mapping of provided name to consumed names. None is treated
        as empty.
    :return: A dict with one sorted tuple of consumed names per provided name.
    """
    if dependencies is None:
        dependencies = {}
    if not isinstance(dependencies, Mapping):
        raise PackagingError(f"{owner} dependencies must be a mapping, got {type(dependencies)}.")
    normalized = {}
    for key, targets in dependencies.items():
        _validate_string(key, f"{owner} dependencies key {key!r}")
        if key not in provides:
            raise PackagingError(
                f"{owner} declares dependencies for '{key}', which is not a provided node."
            )
        resolved = _validate_names(targets, f"{owner} dependencies of '{key}'")
        for target in resolved:
            if target not in known_targets:
                raise PackagingError(f"{owner} node '{key}' depends on unknown name '{target}'.")
        normalized[key] = resolved
    return {node_name: normalized.get(node_name, ()) for node_name in sorted(provides)}


def _topological_order(
    owner: str, provided: set[str], dependencies: Mapping[str, tuple[str, ...]]
) -> list[str]:
    """Topologically sorts provided names by their internal dependency edges.

    Ties are broken alphabetically so the result is deterministic, and the sort is
    iterative so it works however deep the dependency chains are.

    :param owner: Name of the package or manifest, used in the cycle error message.
    :param provided: The names to order.
    :param dependencies: Mapping of provided name to the names it consumes; targets
        outside the provided set are ignored.
    :return: Every provided name, dependencies before dependents.
    """
    internal_edges = {
        node_name: [target for target in targets if target in provided]
        for node_name, targets in dependencies.items()
    }
    remaining_counts = {node_name: len(targets) for node_name, targets in internal_edges.items()}
    dependents = {node_name: [] for node_name in provided}
    for node_name, targets in internal_edges.items():
        for target in targets:
            dependents[target].append(node_name)
    ready = [node_name for node_name, count in remaining_counts.items() if count == 0]
    heapq.heapify(ready)
    ordered = []
    while ready:
        current = heapq.heappop(ready)
        ordered.append(current)
        for dependent in dependents[current]:
            remaining_counts[dependent] -= 1
            if remaining_counts[dependent] == 0:
                heapq.heappush(ready, dependent)
    if len(ordered) != len(provided):
        unordered = sorted(provided - set(ordered))
        raise PackagingError(f"'{owner}' has a dependency cycle involving: {unordered}.")
    return ordered


def _produced_satisfies(expected_type: Any, produced_type: Any) -> bool:
    """Checks that a produced type can be consumed where the expected type is declared.

    This follows Hamilton's edge-type semantics: the produced type may be a subclass of
    the expected type, so a ``bool`` output can feed an ``int`` input but not the
    reverse.

    :param expected_type: The type the consumer declares.
    :param produced_type: The type the producer emits.
    :return: True if the produced value is acceptable for the consumer.
    """
    return htypes.types_match(expected_type, produced_type)


def _mutually_compatible(first_type: Any, second_type: Any) -> bool:
    """Checks that two producer types are interchangeable in either direction.

    :param first_type: One produced type.
    :param second_type: The other produced type.
    :return: True if each type satisfies the other.
    """
    return _produced_satisfies(first_type, second_type) and _produced_satisfies(
        second_type, first_type
    )


class NodePackage:
    """A reusable, self-describing bundle of dataflow nodes.

    A package declares the nodes it provides with their output types, the external
    dependencies it requires with the types it expects, the configuration keys it
    needs, and the dependency edges from each provided node to the names it consumes.
    """

    def __init__(
        self,
        name: str,
        *,
        version: int = 1,
        provides: Mapping[str, Any] = None,
        requires: Mapping[str, Any] = None,
        dependencies: Mapping[str, Iterable[str]] = None,
        config_keys: Iterable[str] = None,
    ):
        """Creates a package from explicit declarations.

        :param name: Name of the package. Must be a non-empty string.
        :param version: Version of the package. Must be an integer of at least 1.
        :param provides: Mapping of provided node name to output type.
        :param requires: Mapping of external dependency name to the expected type.
        :param dependencies: Mapping of provided node name to the iterable of names it
            consumes. Every listed name must be a provided node, a required dependency,
            or a configuration key.
        :param config_keys: Iterable of configuration key names the package needs.
        """
        self.name = _validate_string(name, "Package name")
        self.version = _validate_version(version, f"Package '{self.name}' version")
        self.provides = _validate_type_mapping(provides, f"Package '{self.name}' provides")
        self.requires = _validate_type_mapping(requires, f"Package '{self.name}' requires")
        overlap = set(self.provides) & set(self.requires)
        if overlap:
            raise PackagingError(
                f"Package '{self.name}' cannot both provide and require: {sorted(overlap)}."
            )
        self.config_keys = _validate_names(config_keys, f"Package '{self.name}' config_keys")
        known_targets = set(self.provides) | set(self.requires) | set(self.config_keys)
        self.dependencies = _validate_dependency_edges(
            f"Package '{self.name}'", self.provides, known_targets, dependencies
        )

    @classmethod
    def from_graph(
        cls,
        fn_graph: "graph.FunctionGraph",
        node_names: Iterable[str],
        name: str,
        *,
        version: int = 1,
        include_upstream: bool = False,
    ) -> "NodePackage":
        """Builds a package from a subset of a driver's built internal graph.

        The graph is the one a built driver exposes as ``Driver.graph``. The selected
        nodes become the package's provided nodes; their required dependencies are
        classified as internal edges, external requirements, or configuration keys
        depending on whether the dependency is selected, another graph node, or a
        configuration entry. Optional (defaulted) parameters are ignored.

        :param fn_graph: The driver's built internal graph, i.e. ``Driver.graph``.
        :param node_names: Iterable of node names to package.
        :param name: Name for the new package.
        :param version: Version for the new package.
        :param include_upstream: If True, the selection is expanded to every transitive
            non-input, non-configuration dependency of the selected nodes. The
            expansion is iterative, so it works however deep the graph is.
        :return: The package describing the selected subgraph.
        """
        if not isinstance(fn_graph, graph.FunctionGraph):
            raise PackagingError(
                "from_graph expects the driver's built internal graph (Driver.graph), "
                f"a FunctionGraph -- got {type(fn_graph)}."
            )
        if not isinstance(include_upstream, bool):
            raise PackagingError(
                f"include_upstream must be a boolean, got {type(include_upstream)}."
            )
        selection = list(_validate_names(node_names, "from_graph node_names"))
        if not selection:
            raise PackagingError("from_graph requires at least one node name to package.")
        for node_name in selection:
            if node_name not in fn_graph.nodes:
                raise PackagingError(
                    f"Node '{node_name}' does not exist in the graph, so it cannot be packaged."
                )
            if fn_graph.nodes[node_name].user_defined:
                raise PackagingError(
                    f"Node '{node_name}' is an input to the graph, not a computed node, "
                    "so it cannot be packaged."
                )
        selected = set(selection)
        if include_upstream:
            stack = list(selection)
            while stack:
                current = stack.pop()
                for dep_name, (_, dep_kind) in fn_graph.nodes[current].input_types.items():
                    if dep_kind == DependencyType.OPTIONAL:
                        continue
                    if dep_name in fn_graph.config or dep_name in selected:
                        continue
                    if fn_graph.nodes[dep_name].user_defined:
                        continue
                    selected.add(dep_name)
                    stack.append(dep_name)
        provides = {}
        requires = {}
        dependencies = {}
        config_keys = set()
        for node_name in sorted(selected):
            node_ = fn_graph.nodes[node_name]
            provides[node_name] = node_.type
            edge_targets = []
            for dep_name, (_, dep_kind) in node_.input_types.items():
                if dep_kind == DependencyType.OPTIONAL:
                    continue
                if dep_name in fn_graph.config:
                    config_keys.add(dep_name)
                elif dep_name not in selected:
                    requires[dep_name] = fn_graph.nodes[dep_name].type
                edge_targets.append(dep_name)
            dependencies[node_name] = edge_targets
        return cls(
            name,
            version=version,
            provides=provides,
            requires=requires,
            dependencies=dependencies,
            config_keys=config_keys,
        )

    def dependency_order(self) -> list[str]:
        """Returns the provided nodes in dependency order.

        The order is a topological sort of the package's internal edges, with ties
        broken alphabetically so the result is deterministic. The sort is iterative,
        so it works however deep the package's dependency chains are.

        :return: Every provided node name, dependencies before dependents.
        """
        return _topological_order(self.name, set(self.provides), self.dependencies)

    def manifest(self) -> "PackageManifest":
        """Renders the package as a serializable manifest.

        Types are rendered to strings, and every mapping in the manifest is sorted by
        name so the rendering is deterministic.

        :return: The manifest describing this package.
        """
        return PackageManifest(
            name=self.name,
            version=self.version,
            provides={
                node_name: htypes.get_type_as_string(type_)
                for node_name, type_ in self.provides.items()
            },
            requires={
                dep_name: htypes.get_type_as_string(type_)
                for dep_name, type_ in self.requires.items()
            },
            dependencies=self.dependencies,
            config_keys=self.config_keys,
        )

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, NodePackage) and self.manifest() == other.manifest()

    def __repr__(self) -> str:
        return (
            f"NodePackage(name={self.name!r}, version={self.version}, "
            f"provides={sorted(self.provides)})"
        )


class PackageManifest:
    """The serializable description of a :class:`NodePackage`.

    A manifest holds the same structure as a package, with every type rendered as a
    string. It round-trips losslessly through plain dictionaries and JSON.
    """

    def __init__(
        self,
        name: str,
        version: int,
        provides: Mapping[str, str],
        requires: Mapping[str, str],
        dependencies: Mapping[str, Iterable[str]],
        config_keys: Iterable[str],
    ):
        """Creates a manifest from its fields.

        :param name: Name of the packaged subgraph.
        :param version: Version of the packaged subgraph.
        :param provides: Mapping of provided node name to rendered output type.
        :param requires: Mapping of required dependency name to rendered expected type.
        :param dependencies: Mapping of provided node name to the names it consumes.
        :param config_keys: Iterable of configuration key names.
        """
        self.name = _validate_string(name, "Manifest name")
        self.version = _validate_version(version, f"Manifest '{self.name}' version")
        self.provides = self._validate_string_mapping(provides, "provides")
        self.requires = self._validate_string_mapping(requires, "requires")
        overlap = set(self.provides) & set(self.requires)
        if overlap:
            raise PackagingError(
                f"Manifest '{self.name}' cannot both provide and require: {sorted(overlap)}."
            )
        self.config_keys = _validate_names(config_keys, f"Manifest '{self.name}' config_keys")
        known_targets = set(self.provides) | set(self.requires) | set(self.config_keys)
        self.dependencies = _validate_dependency_edges(
            f"Manifest '{self.name}'", self.provides, known_targets, dependencies
        )

    def _validate_string_mapping(self, value: Any, field: str) -> dict[str, str]:
        """Validates a name-to-rendered-type mapping and returns it sorted.

        :param value: Mapping to check.
        :param field: Manifest field name used in error messages.
        :return: A new dict sorted by key.
        """
        if not isinstance(value, Mapping):
            raise PackagingError(
                f"Manifest '{self.name}' {field} must be a mapping, got {type(value)}."
            )
        for key, rendered in value.items():
            _validate_string(key, f"Manifest '{self.name}' {field} name {key!r}")
            _validate_string(rendered, f"Manifest '{self.name}' {field} type for '{key}'")
        return {key: value[key] for key in sorted(value)}

    def to_dict(self) -> dict[str, Any]:
        """Renders the manifest as a plain, JSON-serializable dictionary.

        :return: A dictionary with every mapping sorted by name.
        """
        return {
            "name": self.name,
            "version": self.version,
            "provides": dict(self.provides),
            "requires": dict(self.requires),
            "dependencies": {
                node_name: list(targets) for node_name, targets in self.dependencies.items()
            },
            "config_keys": list(self.config_keys),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PackageManifest":
        """Reconstructs a manifest from a dictionary produced by :meth:`to_dict`.

        :param data: The dictionary to reconstruct from.
        :return: The reconstructed manifest.
        """
        if not isinstance(data, Mapping):
            raise PackagingError(f"Manifest data must be a mapping, got {type(data)}.")
        unknown = set(data) - set(MANIFEST_FIELDS)
        if unknown:
            raise PackagingError(f"Manifest data has unknown fields: {sorted(unknown)}.")
        missing = set(MANIFEST_FIELDS) - set(data)
        if missing:
            raise PackagingError(f"Manifest data is missing fields: {sorted(missing)}.")
        return cls(
            name=data["name"],
            version=data["version"],
            provides=data["provides"],
            requires=data["requires"],
            dependencies=data["dependencies"],
            config_keys=data["config_keys"],
        )

    def to_json(self) -> str:
        """Renders the manifest as a JSON string.

        :return: The JSON rendering of :meth:`to_dict`.
        """
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, serialized: str) -> "PackageManifest":
        """Reconstructs a manifest from a JSON string produced by :meth:`to_json`.

        :param serialized: The JSON string to reconstruct from.
        :return: The reconstructed manifest.
        """
        if not isinstance(serialized, str):
            raise PackagingError(f"Manifest JSON must be a string, got {type(serialized)}.")
        try:
            data = json.loads(serialized)
        except json.JSONDecodeError as e:
            raise PackagingError(f"Manifest JSON is malformed: {e}.") from e
        return cls.from_dict(data)

    def dependency_order(self) -> list[str]:
        """Returns the provided nodes in dependency order.

        This mirrors :meth:`NodePackage.dependency_order` for manifests that were
        imported rather than built in-process.

        :return: Every provided node name, dependencies before dependents.
        """
        return _topological_order(self.name, set(self.provides), self.dependencies)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, PackageManifest) and self.to_dict() == other.to_dict()

    def __repr__(self) -> str:
        return f"PackageManifest(name={self.name!r}, version={self.version})"


class ValidationProblem:
    """A single problem found while validating a package against a host graph."""

    def __init__(self, category: str, name: str, message: str):
        """Creates a problem record.

        :param category: One of the machine-readable validation categories.
        :param name: The offending node, dependency, or configuration key name; the
            package name for version problems.
        :param message: Human-readable explanation of the problem.
        """
        _validate_string(category, "Problem category")
        if category not in VALIDATION_CATEGORIES:
            raise PackagingError(
                f"Unknown validation category '{category}'. "
                f"Valid categories: {sorted(VALIDATION_CATEGORIES)}."
            )
        self.category = category
        self.name = _validate_string(name, "Problem name")
        self.message = _validate_string(message, "Problem message")

    def __repr__(self) -> str:
        return f"ValidationProblem(category={self.category!r}, name={self.name!r})"


class ValidationReport:
    """The result of validating a package against a host graph."""

    def __init__(self, package_name: str, problems: Iterable[ValidationProblem]):
        """Creates a report from the problems found.

        :param package_name: Name of the validated package.
        :param problems: The problems found; empty if the package is compatible.
        """
        self.package_name = _validate_string(package_name, "Report package_name")
        materialized = list(problems)
        for problem in materialized:
            if not isinstance(problem, ValidationProblem):
                raise PackagingError(
                    f"ValidationReport expects ValidationProblem instances, got {type(problem)}."
                )
        self.problems = tuple(materialized)

    @property
    def is_valid(self) -> bool:
        """Whether the package is compatible with the host graph."""
        return len(self.problems) == 0

    def __str__(self) -> str:
        if self.is_valid:
            return f"Package '{self.package_name}' is compatible with the host graph."
        lines = [f"Package '{self.package_name}' has {len(self.problems)} problem(s):"]
        for problem in self.problems:
            lines.append(f"  [{problem.category}] {problem.message}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"ValidationReport(package_name={self.package_name!r}, problems={len(self.problems)})"
        )


class PackageConflict:
    """A single conflict detected between two packages."""

    def __init__(
        self, first_package: str, second_package: str, category: str, name: str, message: str
    ):
        """Creates a conflict record.

        :param first_package: Name of the first package involved.
        :param second_package: Name of the second package involved.
        :param category: One of the machine-readable conflict categories.
        :param name: The node or dependency name the packages disagree about.
        :param message: Human-readable explanation of the conflict.
        """
        self.first_package = _validate_string(first_package, "Conflict first_package")
        self.second_package = _validate_string(second_package, "Conflict second_package")
        _validate_string(category, "Conflict category")
        if category not in CONFLICT_CATEGORIES:
            raise PackagingError(
                f"Unknown conflict category '{category}'. "
                f"Valid categories: {sorted(CONFLICT_CATEGORIES)}."
            )
        self.category = category
        self.name = _validate_string(name, "Conflict name")
        self.message = _validate_string(message, "Conflict message")

    def __str__(self) -> str:
        return f"[{self.category}] {self.message}"

    def __repr__(self) -> str:
        return (
            f"PackageConflict(category={self.category!r}, name={self.name!r}, "
            f"first_package={self.first_package!r}, second_package={self.second_package!r})"
        )


def validate_package(
    package: NodePackage, fn_graph: "graph.FunctionGraph", minimum_version: int = 1
) -> ValidationReport:
    """Validates a package for compatibility against a host dataflow's graph.

    The graph is the one a built driver exposes as ``Driver.graph``. A required
    dependency is satisfied by a host node whose output type can be consumed where the
    package's expected type is declared, or by a configuration entry of the same name.
    A provided node may share a name with a host input node if its output type is
    acceptable to the host, but may not collide with a computed host node.

    :param package: The package to validate.
    :param fn_graph: The driver's built internal graph, i.e. ``Driver.graph``.
    :param minimum_version: The minimum package version the host accepts. Must be an
        integer of at least 1.
    :return: A report with one problem per incompatibility; empty problems if the
        package is compatible.
    """
    if not isinstance(package, NodePackage):
        raise PackagingError(f"validate_package expects a NodePackage, got {type(package)}.")
    if not isinstance(fn_graph, graph.FunctionGraph):
        raise PackagingError(
            "validate_package expects the driver's built internal graph (Driver.graph), "
            f"a FunctionGraph -- got {type(fn_graph)}."
        )
    _validate_version(minimum_version, "minimum_version")
    problems = []
    if package.version < minimum_version:
        problems.append(
            ValidationProblem(
                "version_too_low",
                package.name,
                f"Package '{package.name}' has version {package.version}, "
                f"but the host requires at least {minimum_version}.",
            )
        )
    for node_name, provided_type in package.provides.items():
        if node_name not in fn_graph.nodes:
            continue
        host_node = fn_graph.nodes[node_name]
        if host_node.user_defined:
            if not _produced_satisfies(host_node.type, provided_type):
                problems.append(
                    ValidationProblem(
                        "dependency_type_mismatch",
                        node_name,
                        f"Package '{package.name}' provides '{node_name}' with type "
                        f"{htypes.get_type_as_string(provided_type)}, but the host expects "
                        f"{htypes.get_type_as_string(host_node.type)}.",
                    )
                )
        else:
            problems.append(
                ValidationProblem(
                    "node_collision",
                    node_name,
                    f"Package '{package.name}' provides '{node_name}', "
                    "which the host graph already computes.",
                )
            )
    for dep_name, expected_type in package.requires.items():
        if dep_name in fn_graph.config:
            continue
        if dep_name not in fn_graph.nodes:
            problems.append(
                ValidationProblem(
                    "missing_dependency",
                    dep_name,
                    f"Package '{package.name}' requires '{dep_name}', which the host graph "
                    "does not define and the configuration does not supply.",
                )
            )
            continue
        produced_type = fn_graph.nodes[dep_name].type
        if not _produced_satisfies(expected_type, produced_type):
            problems.append(
                ValidationProblem(
                    "dependency_type_mismatch",
                    dep_name,
                    f"Package '{package.name}' requires '{dep_name}' with type "
                    f"{htypes.get_type_as_string(expected_type)}, but the host produces "
                    f"{htypes.get_type_as_string(produced_type)}.",
                )
            )
    for config_key in package.config_keys:
        if config_key not in fn_graph.config:
            problems.append(
                ValidationProblem(
                    "config_requirement_missing",
                    config_key,
                    f"Package '{package.name}' needs configuration key '{config_key}', "
                    "which the host configuration does not supply.",
                )
            )
    return ValidationReport(package.name, problems)


def _cross_requirement_conflicts(
    provider: NodePackage, requirer: NodePackage, first: NodePackage, second: NodePackage
) -> list[PackageConflict]:
    """Finds requirement mismatches where one package provides what the other requires.

    :param provider: The package whose provided nodes are checked.
    :param requirer: The package whose requirements are checked.
    :param first: The first package of the original pair, for attribution.
    :param second: The second package of the original pair, for attribution.
    :return: One conflict per mismatched provider/requirer edge.
    """
    conflicts = []
    for dep_name, expected_type in requirer.requires.items():
        if dep_name not in provider.provides:
            continue
        produced_type = provider.provides[dep_name]
        if not _produced_satisfies(expected_type, produced_type):
            conflicts.append(
                PackageConflict(
                    first.name,
                    second.name,
                    "requirement_mismatch",
                    dep_name,
                    f"Package '{requirer.name}' requires '{dep_name}' with type "
                    f"{htypes.get_type_as_string(expected_type)}, but package "
                    f"'{provider.name}' provides it with type "
                    f"{htypes.get_type_as_string(produced_type)}.",
                )
            )
    return conflicts


def find_conflicts(first: NodePackage, second: NodePackage) -> list[PackageConflict]:
    """Detects conflicts between two packages.

    Two packages may provide identically named nodes only when the output types are
    interchangeable in both directions and the recorded dependency names agree. When
    one package provides a node another requires, the provided output type must be
    consumable where the expected type is declared. When both packages require the
    same external dependency, the expected types must be identical.

    :param first: One package.
    :param second: The other package.
    :return: Every detected conflict; an empty list if the packages are compatible.
    """
    if not isinstance(first, NodePackage):
        raise PackagingError(f"find_conflicts expects NodePackage instances, got {type(first)}.")
    if not isinstance(second, NodePackage):
        raise PackagingError(f"find_conflicts expects NodePackage instances, got {type(second)}.")
    conflicts = []
    for node_name in sorted(set(first.provides) & set(second.provides)):
        first_type = first.provides[node_name]
        second_type = second.provides[node_name]
        if not _mutually_compatible(first_type, second_type):
            conflicts.append(
                PackageConflict(
                    first.name,
                    second.name,
                    "duplicate_node",
                    node_name,
                    f"Packages '{first.name}' and '{second.name}' both provide '{node_name}' "
                    f"with incompatible types {htypes.get_type_as_string(first_type)} and "
                    f"{htypes.get_type_as_string(second_type)}.",
                )
            )
        elif first.dependencies[node_name] != second.dependencies[node_name]:
            conflicts.append(
                PackageConflict(
                    first.name,
                    second.name,
                    "duplicate_node",
                    node_name,
                    f"Packages '{first.name}' and '{second.name}' both provide '{node_name}' "
                    "with disagreeing dependencies.",
                )
            )
    conflicts.extend(_cross_requirement_conflicts(first, second, first, second))
    conflicts.extend(_cross_requirement_conflicts(second, first, first, second))
    for dep_name in sorted(set(first.requires) & set(second.requires)):
        if first.requires[dep_name] != second.requires[dep_name]:
            conflicts.append(
                PackageConflict(
                    first.name,
                    second.name,
                    "requirement_disagreement",
                    dep_name,
                    f"Packages '{first.name}' and '{second.name}' both require '{dep_name}' "
                    f"but expect different types "
                    f"{htypes.get_type_as_string(first.requires[dep_name])} and "
                    f"{htypes.get_type_as_string(second.requires[dep_name])}.",
                )
            )
    return conflicts


def _find_all_conflicts(packages: list[NodePackage]) -> list[PackageConflict]:
    """Detects conflicts across every pair of the given packages.

    :param packages: The packages to cross-check.
    :return: Every conflict from every pair.
    """
    all_conflicts = []
    for index, first in enumerate(packages):
        for second in packages[index + 1 :]:
            all_conflicts.extend(find_conflicts(first, second))
    return all_conflicts


def compose_packages(
    packages: Iterable[NodePackage], name: str, *, version: int = None
) -> NodePackage:
    """Composes multiple packages into a single package.

    Every pair of packages is checked for conflicts before any merging happens, so
    composition either fails with the complete set of conflicts or succeeds with a
    result that is identical for any ordering of the input packages. Requirements
    satisfied by another package's provided nodes become internal edges of the
    composed package.

    :param packages: The packages to compose. Must contain at least one package.
    :param name: Name for the composed package.
    :param version: Version for the composed package. Defaults to the highest version
        among the composed packages.
    :return: The composed package.
    """
    materialized = list(packages)
    for package in materialized:
        if not isinstance(package, NodePackage):
            raise PackagingError(
                f"compose_packages expects NodePackage instances, got {type(package)}."
            )
    if not materialized:
        raise PackagingError("compose_packages requires at least one package.")
    _validate_string(name, "Composed package name")
    if version is not None:
        _validate_version(version, "Composed package version")
    all_conflicts = _find_all_conflicts(materialized)
    if all_conflicts:
        raise PackageConflictError(all_conflicts)
    provides = {}
    dependencies = {}
    requires = {}
    config_keys = set()
    for package in materialized:
        provides.update(package.provides)
        dependencies.update(package.dependencies)
        requires.update(package.requires)
        config_keys.update(package.config_keys)
    external_requires = {
        dep_name: expected_type
        for dep_name, expected_type in requires.items()
        if dep_name not in provides
    }
    return NodePackage(
        name,
        version=version if version is not None else max(p.version for p in materialized),
        provides=provides,
        requires=external_requires,
        dependencies=dependencies,
        config_keys=config_keys,
    )


def _mapping_diff(
    old: Mapping[str, str], new: Mapping[str, str]
) -> tuple[dict[str, str], dict[str, str], dict[str, tuple[str, str]]]:
    """Computes the added, removed, and changed entries between two sorted mappings.

    :param old: The mapping from the older manifest.
    :param new: The mapping from the newer manifest.
    :return: Added entries, removed entries, and changed entries as name to
        (old rendering, new rendering).
    """
    added = {name: new[name] for name in sorted(set(new) - set(old))}
    removed = {name: old[name] for name in sorted(set(old) - set(new))}
    changed = {
        name: (old[name], new[name])
        for name in sorted(set(old) & set(new))
        if old[name] != new[name]
    }
    return added, removed, changed


class ManifestDiff:
    """The structural differences between two package manifests."""

    def __init__(self, old: PackageManifest, new: PackageManifest):
        """Computes the diff between two manifests.

        :param old: The manifest treated as the older revision.
        :param new: The manifest treated as the newer revision.
        """
        if not isinstance(old, PackageManifest):
            raise PackagingError(
                f"ManifestDiff expects PackageManifest instances, got {type(old)}."
            )
        if not isinstance(new, PackageManifest):
            raise PackagingError(
                f"ManifestDiff expects PackageManifest instances, got {type(new)}."
            )
        self.added_nodes, self.removed_nodes, self.changed_nodes = _mapping_diff(
            old.provides, new.provides
        )
        self.added_requirements, self.removed_requirements, self.changed_requirements = (
            _mapping_diff(old.requires, new.requires)
        )
        self.added_config_keys = tuple(sorted(set(new.config_keys) - set(old.config_keys)))
        self.removed_config_keys = tuple(sorted(set(old.config_keys) - set(new.config_keys)))

    @property
    def has_changes(self) -> bool:
        """Whether the two manifests differ on any of the compared axes."""
        return any(
            [
                self.added_nodes,
                self.removed_nodes,
                self.changed_nodes,
                self.added_requirements,
                self.removed_requirements,
                self.changed_requirements,
                self.added_config_keys,
                self.removed_config_keys,
            ]
        )


def diff_manifests(old: PackageManifest, new: PackageManifest) -> ManifestDiff:
    """Computes the structural differences between two package manifests.

    :param old: The manifest treated as the older revision.
    :param new: The manifest treated as the newer revision.
    :return: The diff between the two manifests.
    """
    return ManifestDiff(old, new)


def export_package(package: NodePackage, path: str | pathlib.Path) -> None:
    """Exports a package's manifest to a JSON file.

    :param package: The package to export.
    :param path: The file path to write the manifest to.
    """
    if not isinstance(package, NodePackage):
        raise PackagingError(f"export_package expects a NodePackage, got {type(package)}.")
    pathlib.Path(path).write_text(package.manifest().to_json() + "\n", encoding="utf-8")


def import_manifest(path: str | pathlib.Path) -> PackageManifest:
    """Imports a package manifest from a JSON file written by :func:`export_package`.

    :param path: The file path to read the manifest from.
    :return: The imported manifest.
    """
    return PackageManifest.from_json(pathlib.Path(path).read_text(encoding="utf-8"))
