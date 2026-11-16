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

import functools
import itertools
import json
import sys
import typing

import pytest

from hamilton import ad_hoc_utils, async_driver, driver, htypes
from hamilton import function_modifiers as fm

try:
    from hamilton import packaging
    from hamilton.packaging import (
        CONFLICT_CATEGORIES,
        MANIFEST_FIELDS,
        VALIDATION_CATEGORIES,
        ManifestDiff,
        NodePackage,
        PackageConflict,
        PackageConflictError,
        PackageManifest,
        PackageValidationError,
        PackagingError,
        ValidationProblem,
        ValidationReport,
        compose_packages,
        diff_manifests,
        export_package,
        find_conflicts,
        import_manifest,
        validate_package,
    )
except ImportError:
    packaging = None
    CONFLICT_CATEGORIES = None
    MANIFEST_FIELDS = None
    VALIDATION_CATEGORIES = None
    ManifestDiff = None
    NodePackage = None
    PackageConflict = None
    PackageConflictError = None
    PackageManifest = None
    PackageValidationError = None
    PackagingError = None
    ValidationProblem = None
    ValidationReport = None
    compose_packages = None
    diff_manifests = None
    export_package = None
    find_conflicts = None
    import_manifest = None
    validate_package = None


def base_int() -> int:
    return 1


def doubled(base_int: int) -> int:
    return base_int * 2


def as_float(doubled: int) -> float:
    return float(doubled)


def scaled(base_int: int, factor: int) -> int:
    return base_int * factor


def with_default(base_int: int, offset: int = 3) -> int:
    return base_int + offset


def needs_input(external_num: int) -> int:
    return external_num + 1


def uses_flag_input(external_flag: bool) -> int:
    return int(external_flag)


def optional_source() -> int:
    return 9


def optional_consumer(base_int: int, optional_source: int = 5) -> int:
    return base_int + optional_source


def any_node() -> typing.Any:
    return 1


def consumes_any(any_node: int) -> int:
    return any_node


def listy_node() -> list[int]:
    return [1, 2]


def flag_node() -> bool:
    return True


def from_flag(flag_node: int) -> int:
    return flag_node + 1


def _build_driver(*fns, config=None):
    module = ad_hoc_utils.create_temporary_module(*fns)
    return driver.Builder().with_modules(module).with_config(config or {}).build()


def _simple_package(name="pkg", **overrides):
    kwargs = dict(
        version=1,
        provides={"doubled": int, "as_float": float},
        requires={"base_int": int},
        dependencies={"doubled": ["base_int"], "as_float": ["doubled"]},
        config_keys=["factor"],
    )
    kwargs.update(overrides)
    return NodePackage(name, **kwargs)


def chain_step(prev: float) -> float:
    return prev + 1.0


@functools.lru_cache(maxsize=1)
def _deep_chain_state():
    chain_size = sys.getrecursionlimit() + 200
    parameterization = {}
    for i in range(chain_size):
        parameterization[f"node_{i}"] = {
            "prev": fm.source(f"node_{i - 1}") if i > 0 else fm.value(0.0)
        }
    decorated = fm.parameterize(**parameterization)(chain_step)
    module = ad_hoc_utils.create_temporary_module(decorated, module_name="pkg_large_chain")
    dr = driver.Builder().with_modules(module).build()
    return chain_size, dr


class TestNodePackageConstructor:
    def test_defaults_via_empty_manifest(self):
        package = NodePackage("empty")
        assert package.manifest().to_dict() == {
            "name": "empty",
            "version": 1,
            "provides": {},
            "requires": {},
            "dependencies": {},
            "config_keys": [],
        }

    def test_attributes_exposed(self):
        package = _simple_package()
        assert package.name == "pkg"
        assert package.version == 1
        assert set(package.provides) == {"doubled", "as_float"}
        assert package.provides["doubled"] is int
        assert set(package.requires) == {"base_int"}
        assert set(package.config_keys) == {"factor"}
        assert set(package.dependencies["doubled"]) == {"base_int"}

    def test_non_string_name(self):
        with pytest.raises(PackagingError):
            NodePackage(123)

    def test_empty_name(self):
        with pytest.raises(PackagingError):
            NodePackage("")

    def test_string_version(self):
        with pytest.raises(PackagingError):
            NodePackage("p", version="2")

    def test_zero_version(self):
        with pytest.raises(PackagingError):
            NodePackage("p", version=0)

    def test_bool_version(self):
        with pytest.raises(PackagingError):
            NodePackage("p", version=True)

    def test_float_version(self):
        with pytest.raises(PackagingError):
            NodePackage("p", version=1.5)

    def test_provides_not_a_mapping(self):
        with pytest.raises(PackagingError):
            NodePackage("p", provides=["a"])

    def test_provides_non_string_key(self):
        with pytest.raises(PackagingError):
            NodePackage("p", provides={1: int})

    def test_provides_string_value(self):
        with pytest.raises(PackagingError):
            NodePackage("p", provides={"a": "int"})

    def test_provides_int_value(self):
        with pytest.raises(PackagingError):
            NodePackage("p", provides={"a": 5})

    def test_provides_generic_and_any_values(self):
        package = NodePackage("p", provides={"a": list[int], "b": typing.Any})
        assert set(package.provides) == {"a", "b"}

    def test_requires_not_a_mapping(self):
        with pytest.raises(PackagingError):
            NodePackage("p", requires=[("a", int)])

    def test_requires_non_string_key(self):
        with pytest.raises(PackagingError):
            NodePackage("p", requires={2: int})

    def test_requires_string_value(self):
        with pytest.raises(PackagingError):
            NodePackage("p", requires={"a": "float"})

    def test_provides_requires_overlap(self):
        with pytest.raises(PackagingError):
            NodePackage("p", provides={"a": int}, requires={"a": int})

    def test_config_keys_plain_string(self):
        with pytest.raises(PackagingError):
            NodePackage("p", config_keys="factor")

    def test_config_keys_non_string_entry(self):
        with pytest.raises(PackagingError):
            NodePackage("p", config_keys=["factor", 7])

    def test_config_keys_generator_single_pass(self):
        package = NodePackage("p", config_keys=(key for key in ["b_key", "a_key"]))
        assert set(package.config_keys) == {"a_key", "b_key"}

    def test_dependencies_not_a_mapping(self):
        with pytest.raises(PackagingError):
            NodePackage("p", provides={"a": int}, dependencies=["a"])

    def test_dependencies_key_not_provided(self):
        with pytest.raises(PackagingError):
            NodePackage("p", provides={"a": int}, dependencies={"b": []})

    def test_dependencies_unknown_target(self):
        with pytest.raises(PackagingError):
            NodePackage("p", provides={"a": int}, dependencies={"a": ["mystery"]})

    def test_dependencies_non_iterable_value(self):
        with pytest.raises(PackagingError):
            NodePackage("p", provides={"a": int}, dependencies={"a": 5})

    def test_dependencies_generator_single_pass(self):
        package = NodePackage(
            "p",
            provides={"x": int},
            requires={"a": int, "b": int},
            dependencies={"x": (name for name in ["b", "a"])},
        )
        assert set(package.dependencies["x"]) == {"a", "b"}

    def test_dependencies_may_reference_all_boundary_kinds(self):
        package = NodePackage(
            "p",
            provides={"a": int, "b": int},
            requires={"ext": int},
            config_keys=["cfg"],
            dependencies={"b": ["a", "ext", "cfg"]},
        )
        assert set(package.dependencies["b"]) == {"a", "ext", "cfg"}
        assert not package.dependencies.get("a")


class TestFromGraph:
    def test_rejects_hamilton_graph(self):
        dr = _build_driver(base_int, doubled)
        with pytest.raises(PackagingError):
            NodePackage.from_graph(dr.get_graph(), ["doubled"], "p")

    def test_rejects_plain_dict(self):
        with pytest.raises(PackagingError):
            NodePackage.from_graph({}, ["doubled"], "p")

    def test_basic_selection(self):
        dr = _build_driver(base_int, doubled, as_float)
        package = NodePackage.from_graph(dr.graph, ["doubled", "as_float"], "p")
        assert set(package.provides) == {"doubled", "as_float"}
        assert package.provides["as_float"] is float
        assert set(package.requires) == {"base_int"}
        assert package.requires["base_int"] is int
        assert set(package.dependencies["doubled"]) == {"base_int"}
        assert set(package.dependencies["as_float"]) == {"doubled"}

    def test_unknown_node(self):
        dr = _build_driver(base_int)
        with pytest.raises(PackagingError):
            NodePackage.from_graph(dr.graph, ["nonexistent"], "p")

    def test_input_node_rejected(self):
        dr = _build_driver(needs_input)
        with pytest.raises(PackagingError):
            NodePackage.from_graph(dr.graph, ["external_num"], "p")

    def test_empty_selection(self):
        dr = _build_driver(base_int)
        with pytest.raises(PackagingError):
            NodePackage.from_graph(dr.graph, [], "p")

    def test_non_iterable_selection(self):
        dr = _build_driver(base_int)
        with pytest.raises(PackagingError):
            NodePackage.from_graph(dr.graph, 5, "p")

    def test_non_bool_include_upstream(self):
        dr = _build_driver(base_int)
        with pytest.raises(PackagingError):
            NodePackage.from_graph(dr.graph, ["base_int"], "p", include_upstream=1)

    def test_include_upstream_expands_selection(self):
        dr = _build_driver(base_int, doubled, as_float)
        package = NodePackage.from_graph(dr.graph, ["as_float"], "p", include_upstream=True)
        assert set(package.provides) == {"base_int", "doubled", "as_float"}
        assert not package.requires

    def test_include_upstream_shared_ancestor_once(self):
        dr = _build_driver(base_int, doubled, as_float, with_default)
        package = NodePackage.from_graph(
            dr.graph, ["as_float", "with_default"], "p", include_upstream=True
        )
        assert set(package.provides) == {"base_int", "doubled", "as_float", "with_default"}
        assert not package.requires
        order = package.dependency_order()
        assert order.index("base_int") < order.index("doubled") < order.index("as_float")

    def test_include_upstream_skips_optional_computed_producer(self):
        dr = _build_driver(base_int, optional_source, optional_consumer)
        package = NodePackage.from_graph(
            dr.graph, ["optional_consumer"], "p", include_upstream=True
        )
        assert "optional_source" not in package.provides
        assert set(package.provides) == {"base_int", "optional_consumer"}

    def test_include_upstream_stops_at_inputs(self):
        dr = _build_driver(needs_input, doubled)
        package = NodePackage.from_graph(dr.graph, ["needs_input"], "p", include_upstream=True)
        assert set(package.provides) == {"needs_input"}
        assert set(package.requires) == {"external_num"}

    def test_config_dependency_recorded_as_config_key(self):
        dr = _build_driver(base_int, scaled, config={"factor": 2})
        package = NodePackage.from_graph(dr.graph, ["scaled"], "p")
        assert set(package.config_keys) == {"factor"}
        assert "factor" not in package.requires
        assert set(package.requires) == {"base_int"}
        assert set(package.dependencies["scaled"]) == {"base_int", "factor"}

    def test_requirement_typed_by_producing_node(self):
        dr = _build_driver(flag_node, from_flag)
        package = NodePackage.from_graph(dr.graph, ["from_flag"], "p")
        assert package.requires["flag_node"] is bool

    def test_config_key_edge_survives_manifest_round_trip(self):
        dr = _build_driver(base_int, scaled, config={"factor": 2})
        package = NodePackage.from_graph(dr.graph, ["scaled"], "p")
        data = package.manifest().to_dict()
        assert set(data["dependencies"]["scaled"]) == {"base_int", "factor"}
        assert set(data["config_keys"]) == {"factor"}
        assert PackageManifest.from_dict(data) == package.manifest()

    def test_optional_parameter_ignored(self):
        dr = _build_driver(base_int, with_default)
        package = NodePackage.from_graph(dr.graph, ["with_default"], "p")
        assert "offset" not in package.requires
        assert set(package.dependencies["with_default"]) == {"base_int"}

    def test_version_passed_through(self):
        dr = _build_driver(base_int)
        package = NodePackage.from_graph(dr.graph, ["base_int"], "p", version=4)
        assert package.version == 4

    def test_selection_accepts_generator(self):
        dr = _build_driver(base_int, doubled)
        package = NodePackage.from_graph(dr.graph, (n for n in ["doubled"]), "p")
        assert set(package.provides) == {"doubled"}

    def test_selection_names_must_be_strings(self):
        dr = _build_driver(base_int)
        with pytest.raises(PackagingError):
            NodePackage.from_graph(dr.graph, [1], "p")

    def test_deep_chain_no_recursion_error(self):
        chain_size, dr = _deep_chain_state()
        final_node = f"node_{chain_size - 1}"
        package = NodePackage.from_graph(dr.graph, [final_node], "deep", include_upstream=True)
        assert len(package.provides) == chain_size
        order = package.dependency_order()
        assert len(order) == chain_size
        assert order[0] == "node_0"
        assert order[-1] == final_node


class TestDependencyOrder:
    def test_dependencies_before_dependents(self):
        package = _simple_package()
        order = package.dependency_order()
        assert set(order) == {"doubled", "as_float"}
        assert order.index("doubled") < order.index("as_float")

    def test_alphabetical_tie_break(self):
        package = NodePackage("p", provides={"zeta": int, "alpha": int})
        assert package.dependency_order() == ["alpha", "zeta"]

    def test_empty_package(self):
        assert NodePackage("p").dependency_order() == []

    def test_cycle_detected(self):
        package = NodePackage(
            "p",
            provides={"a": int, "b": int},
            dependencies={"a": ["b"], "b": ["a"]},
        )
        with pytest.raises(PackagingError):
            package.dependency_order()

    def test_manifest_cycle_detected(self):
        manifest = PackageManifest.from_dict(
            {
                "name": "m",
                "version": 1,
                "provides": {"a": "int", "b": "int"},
                "requires": {},
                "dependencies": {"a": ["b"], "b": ["a"]},
                "config_keys": [],
            }
        )
        with pytest.raises(PackagingError):
            manifest.dependency_order()

    def test_imported_manifest_dependency_order(self, tmp_path):
        package = _simple_package()
        path = tmp_path / "ordered.json"
        export_package(package, path)
        order = import_manifest(path).dependency_order()
        assert set(order) == {"doubled", "as_float"}
        assert order.index("doubled") < order.index("as_float")

    def test_manifest_dependency_order_matches_package(self):
        package = _simple_package()
        assert package.manifest().dependency_order() == package.dependency_order()


class TestManifest:
    def test_manifest_is_package_manifest(self):
        assert isinstance(_simple_package().manifest(), PackageManifest)

    def test_type_strings_use_get_type_as_string(self):
        package = NodePackage(
            "p",
            provides={"a": int, "b": list[int]},
            requires={"c": dict[str, float]},
            dependencies={"a": ["c"]},
        )
        data = package.manifest().to_dict()
        assert data["provides"]["a"] == htypes.get_type_as_string(int)
        assert data["provides"]["b"] == htypes.get_type_as_string(list[int])
        assert data["requires"]["c"] == htypes.get_type_as_string(dict[str, float])

    def test_mappings_sorted(self):
        package = NodePackage(
            "p",
            provides={"zeta": int, "alpha": int, "mid": int},
            requires={"z_req": int, "a_req": int},
            dependencies={"mid": ["zeta", "a_req"]},
        )
        data = package.manifest().to_dict()
        assert list(data["provides"]) == sorted(data["provides"])
        assert list(data["requires"]) == sorted(data["requires"])
        assert list(data["dependencies"]) == sorted(data["dependencies"])
        assert data["dependencies"]["mid"] == sorted(data["dependencies"]["mid"])
        assert data["config_keys"] == sorted(data["config_keys"])

    def test_json_round_trip(self):
        manifest = _simple_package().manifest()
        assert json.loads(manifest.to_json()) == manifest.to_dict()

    def test_from_dict_round_trip(self):
        manifest = _simple_package().manifest()
        assert PackageManifest.from_dict(manifest.to_dict()) == manifest

    def test_from_json_round_trip(self):
        manifest = _simple_package().manifest()
        reloaded = PackageManifest.from_json(manifest.to_json())
        assert reloaded == manifest
        assert reloaded.to_dict() == manifest.to_dict()

    def test_from_dict_unknown_field(self):
        data = _simple_package().manifest().to_dict()
        data["surprise"] = 1
        with pytest.raises(PackagingError):
            PackageManifest.from_dict(data)

    def test_from_dict_missing_field(self):
        data = _simple_package().manifest().to_dict()
        del data["provides"]
        with pytest.raises(PackagingError):
            PackageManifest.from_dict(data)

    def test_from_dict_dependency_target_non_string(self):
        data = _simple_package().manifest().to_dict()
        data["dependencies"]["doubled"] = ["base_int", 7]
        with pytest.raises(PackagingError):
            PackageManifest.from_dict(data)

    def test_from_dict_config_keys_bare_string(self):
        data = _simple_package().manifest().to_dict()
        data["config_keys"] = "factor"
        with pytest.raises(PackagingError):
            PackageManifest.from_dict(data)

    def test_from_json_malformed_inner_payload(self):
        data = _simple_package().manifest().to_dict()
        data["dependencies"]["doubled"] = ["base_int", 7]
        with pytest.raises(PackagingError):
            PackageManifest.from_json(json.dumps(data))

    def test_from_dict_non_mapping(self):
        with pytest.raises(PackagingError):
            PackageManifest.from_dict([1, 2])

    def test_from_json_non_string(self):
        with pytest.raises(PackagingError):
            PackageManifest.from_json(42)

    def test_from_json_malformed(self):
        with pytest.raises(PackagingError):
            PackageManifest.from_json("{not valid json")

    def test_constructor_non_string_name(self):
        with pytest.raises(PackagingError):
            PackageManifest(9, 1, {}, {}, {}, [])

    def test_constructor_bad_version(self):
        with pytest.raises(PackagingError):
            PackageManifest("m", "1", {}, {}, {}, [])

    def test_constructor_provides_non_mapping(self):
        with pytest.raises(PackagingError):
            PackageManifest("m", 1, ["a"], {}, {}, [])

    def test_constructor_provides_requires_overlap(self):
        with pytest.raises(PackagingError):
            PackageManifest("m", 1, {"a": "int"}, {"a": "int"}, {}, [])

    def test_constructor_requires_non_string_key(self):
        with pytest.raises(PackagingError):
            PackageManifest("m", 1, {}, {3: "int"}, {}, [])

    def test_constructor_dependencies_non_mapping(self):
        with pytest.raises(PackagingError):
            PackageManifest("m", 1, {"a": "int"}, {}, ["a"], [])

    def test_constructor_dependencies_key_not_provided(self):
        with pytest.raises(PackagingError):
            PackageManifest("m", 1, {"a": "int"}, {}, {"b": []}, [])

    def test_constructor_dependencies_unknown_target(self):
        with pytest.raises(PackagingError):
            PackageManifest("m", 1, {"a": "int"}, {}, {"a": ["ghost"]}, [])

    def test_constructor_config_keys_plain_string(self):
        with pytest.raises(PackagingError):
            PackageManifest("m", 1, {}, {}, {}, "cfg")

    def test_equality_negative_on_version(self):
        first = NodePackage("p", version=1).manifest()
        second = NodePackage("p", version=2).manifest()
        assert first != second

    def test_equality_negative_on_other_type(self):
        assert NodePackage("p").manifest() != {"name": "p"}

    def test_package_equality(self):
        assert _simple_package() == _simple_package()
        assert _simple_package() != _simple_package(version=2)
        assert _simple_package() != "pkg"


class TestExportImport:
    def test_round_trip(self, tmp_path):
        package = _simple_package()
        path = tmp_path / "pkg.json"
        export_package(package, path)
        imported = import_manifest(path)
        assert imported == package.manifest()

    def test_exported_file_is_json(self, tmp_path):
        package = _simple_package()
        path = tmp_path / "pkg.json"
        export_package(package, str(path))
        with open(path, encoding="utf-8") as f:
            assert json.load(f) == package.manifest().to_dict()

    def test_round_trip_with_string_path(self, tmp_path):
        package = _simple_package()
        path = tmp_path / "pkg_str.json"
        export_package(package, str(path))
        assert import_manifest(str(path)) == package.manifest()

    def test_export_rejects_non_package(self, tmp_path):
        with pytest.raises(PackagingError):
            export_package({"name": "p"}, tmp_path / "pkg.json")

    def test_import_unknown_field(self, tmp_path):
        data = _simple_package().manifest().to_dict()
        data["surprise"] = 1
        path = tmp_path / "unknown.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(PackagingError):
            import_manifest(path)

    def test_import_semantically_invalid_dependency(self, tmp_path):
        data = _simple_package().manifest().to_dict()
        data["dependencies"]["not_provided"] = []
        path = tmp_path / "bad_dep.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(PackagingError):
            import_manifest(path)

    def test_import_missing_field(self, tmp_path):
        data = _simple_package().manifest().to_dict()
        del data["provides"]
        path = tmp_path / "missing.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(PackagingError):
            import_manifest(path)

    def test_import_malformed_json(self, tmp_path):
        path = tmp_path / "broken.json"
        path.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(PackagingError):
            import_manifest(path)

    def test_import_hand_written_manifest(self, tmp_path):
        data = {
            "name": "hand",
            "version": 2,
            "provides": {"a": "int"},
            "requires": {"b": "float"},
            "dependencies": {"a": ["b"]},
            "config_keys": ["cfg"],
        }
        path = tmp_path / "hand.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        manifest = import_manifest(path)
        assert manifest.name == "hand"
        assert manifest.version == 2
        assert manifest.to_dict() == data


class TestValidatePackage:
    def test_rejects_non_package(self):
        dr = _build_driver(base_int)
        with pytest.raises(PackagingError):
            validate_package("pkg", dr.graph)

    def test_rejects_hamilton_graph(self):
        dr = _build_driver(base_int)
        package = NodePackage("p", requires={"base_int": int})
        with pytest.raises(PackagingError):
            validate_package(package, dr.get_graph())

    def test_rejects_non_int_minimum_version(self):
        dr = _build_driver(base_int)
        with pytest.raises(PackagingError):
            validate_package(NodePackage("p"), dr.graph, minimum_version="1")

    def test_rejects_bool_minimum_version(self):
        dr = _build_driver(base_int)
        with pytest.raises(PackagingError):
            validate_package(NodePackage("p"), dr.graph, minimum_version=True)

    def test_rejects_zero_minimum_version(self):
        dr = _build_driver(base_int)
        with pytest.raises(PackagingError):
            validate_package(NodePackage("p"), dr.graph, minimum_version=0)

    def test_compatible_package(self):
        dr = _build_driver(base_int)
        package = NodePackage(
            "p",
            provides={"enrichment": float},
            requires={"base_int": int},
            dependencies={"enrichment": ["base_int"]},
        )
        report = validate_package(package, dr.graph)
        assert isinstance(report, ValidationReport)
        assert report.package_name == "p"
        assert report.is_valid is True
        assert not report.problems

    def test_missing_dependency_flagged(self):
        dr = _build_driver(base_int)
        package = NodePackage("p", requires={"absent_upstream": int})
        report = validate_package(package, dr.graph)
        assert report.is_valid is False
        by_name = {problem.name: problem for problem in report.problems}
        assert by_name["absent_upstream"].category == "missing_dependency"

    def test_missing_dependency_not_flagged_when_present(self):
        dr = _build_driver(base_int)
        package = NodePackage("p", requires={"base_int": int})
        report = validate_package(package, dr.graph)
        assert report.is_valid is True

    def test_conflict_mismatch_message_names_offender(self):
        provider = NodePackage("a", provides={"shared": int})
        requirer = NodePackage("b", requires={"shared": bool})
        conflicts = find_conflicts(provider, requirer)
        by_name = {c.name: c for c in conflicts}
        assert "shared" in str(by_name["shared"])

    def test_requirement_type_mismatch_flagged(self):
        dr = _build_driver(base_int)
        package = NodePackage("p", requires={"base_int": bool})
        report = validate_package(package, dr.graph)
        by_name = {problem.name: problem for problem in report.problems}
        assert by_name["base_int"].category == "dependency_type_mismatch"

    def test_bool_output_feeds_int_requirement(self):
        dr = _build_driver(flag_node)
        package = NodePackage("p", requires={"flag_node": int})
        report = validate_package(package, dr.graph)
        assert report.is_valid is True

    def test_provided_bool_feeds_int_host_input(self):
        dr = _build_driver(needs_input)
        package = NodePackage("p", provides={"external_num": bool})
        report = validate_package(package, dr.graph)
        assert report.is_valid is True

    def test_provided_int_cannot_feed_bool_host_input(self):
        dr = _build_driver(uses_flag_input)
        package = NodePackage("p", provides={"external_flag": int})
        report = validate_package(package, dr.graph)
        by_name = {problem.name: problem for problem in report.problems}
        assert by_name["external_flag"].category == "dependency_type_mismatch"

    def test_generic_alias_requirement_matches(self):
        dr = _build_driver(listy_node)
        assert validate_package(
            NodePackage("p", requires={"listy_node": list[int]}), dr.graph
        ).is_valid
        mismatched = validate_package(
            NodePackage("p", requires={"listy_node": dict[str, int]}), dr.graph
        )
        by_name = {problem.name: problem for problem in mismatched.problems}
        assert by_name["listy_node"].category == "dependency_type_mismatch"

    def test_any_host_producer_satisfies_typed_requirement(self):
        dr = _build_driver(any_node, consumes_any)
        report = validate_package(NodePackage("p", requires={"any_node": int}), dr.graph)
        assert report.is_valid is True

    def test_any_provided_satisfies_typed_host_input(self):
        dr = _build_driver(needs_input)
        report = validate_package(NodePackage("p", provides={"external_num": typing.Any}), dr.graph)
        assert report.is_valid is True

    def test_any_requirement_accepts_any_producer(self):
        dr = _build_driver(listy_node)
        report = validate_package(NodePackage("p", requires={"listy_node": typing.Any}), dr.graph)
        assert report.is_valid is True

    def test_node_collision_flagged(self):
        dr = _build_driver(base_int)
        package = NodePackage("p", provides={"base_int": int})
        report = validate_package(package, dr.graph)
        by_name = {problem.name: problem for problem in report.problems}
        assert by_name["base_int"].category == "node_collision"

    def test_provided_type_checked_against_config_host_input(self):
        dr = _build_driver(base_int, scaled, config={"factor": 2})
        report = validate_package(NodePackage("p", provides={"factor": str}), dr.graph)
        by_name = {problem.name: problem for problem in report.problems}
        assert by_name["factor"].category == "dependency_type_mismatch"

    def test_provided_matching_type_over_config_host_input_ok(self):
        dr = _build_driver(base_int, scaled, config={"factor": 2})
        report = validate_package(NodePackage("p", provides={"factor": int}), dr.graph)
        assert report.is_valid is True

    def test_no_collision_for_fresh_name(self):
        dr = _build_driver(base_int)
        package = NodePackage("p", provides={"brand_new": int})
        report = validate_package(package, dr.graph)
        assert report.is_valid is True

    def test_config_requirement_missing_flagged(self):
        dr = _build_driver(base_int)
        package = NodePackage("p", config_keys=["absent_key"])
        report = validate_package(package, dr.graph)
        by_name = {problem.name: problem for problem in report.problems}
        assert by_name["absent_key"].category == "config_requirement_missing"

    def test_config_requirement_present(self):
        dr = _build_driver(base_int, scaled, config={"factor": 2})
        package = NodePackage("p", config_keys=["factor"])
        report = validate_package(package, dr.graph)
        assert report.is_valid is True

    def test_undeclared_dependency_satisfied_by_config(self):
        dr = _build_driver(base_int, scaled, config={"factor": 2})
        package = NodePackage("p", requires={"factor": int})
        report = validate_package(package, dr.graph)
        assert report.is_valid is True

    def test_config_satisfies_requirement_regardless_of_type(self):
        dr = _build_driver(base_int, scaled, config={"factor": 2})
        package = NodePackage("p", requires={"factor": str})
        report = validate_package(package, dr.graph)
        assert report.is_valid is True

    def test_mixed_problems_aggregate(self):
        dr = _build_driver(base_int, scaled, config={"factor": 2})
        package = NodePackage(
            "p",
            provides={"scaled": int},
            requires={"factor": int, "truly_missing": int, "base_int": bool},
            config_keys=["factor", "missing_key"],
        )
        report = validate_package(package, dr.graph)
        assert report.is_valid is False
        assert len(report.problems) >= 3
        by_name = {problem.name: problem for problem in report.problems}
        assert by_name["truly_missing"].category == "missing_dependency"
        assert by_name["base_int"].category == "dependency_type_mismatch"
        assert by_name["missing_key"].category == "config_requirement_missing"
        assert by_name["scaled"].category == "node_collision"
        assert "factor" not in by_name

    def test_version_too_low(self):
        dr = _build_driver(base_int)
        package = NodePackage("p", version=2)
        report = validate_package(package, dr.graph, minimum_version=3)
        by_name = {problem.name: problem for problem in report.problems}
        assert by_name["p"].category == "version_too_low"
        assert "2" in by_name["p"].message
        assert "3" in by_name["p"].message

    def test_problem_attributes_populated_by_validation(self):
        dr = _build_driver(base_int)
        package = NodePackage("attr_pkg", requires={"absent_one": int})
        report = validate_package(package, dr.graph)
        problem = report.problems[0]
        assert problem.category in set(VALIDATION_CATEGORIES)
        assert problem.name == "absent_one"
        assert isinstance(problem.message, str)

    def test_version_boundary_equal_passes(self):
        dr = _build_driver(base_int)
        package = NodePackage("p", version=3)
        report = validate_package(package, dr.graph, minimum_version=3)
        assert report.is_valid is True

    def test_optional_parameter_not_flagged(self):
        dr = _build_driver(base_int)
        host = _build_driver(base_int, with_default)
        package = NodePackage.from_graph(host.graph, ["with_default"], "p")
        report = validate_package(package, dr.graph)
        by_name = {problem.name: problem for problem in report.problems}
        assert "offset" not in by_name

    def test_report_str_contains_offenders(self):
        dr = _build_driver(base_int)
        package = NodePackage("lonely_pkg", requires={"vanished": int})
        report = validate_package(package, dr.graph)
        assert "lonely_pkg" in str(report)

    def test_valid_report_str(self):
        dr = _build_driver(base_int)
        report = validate_package(NodePackage("wholesome"), dr.graph)
        assert "wholesome" in str(report)

    def test_categories_constant(self):
        assert set(VALIDATION_CATEGORIES) == {
            "version_too_low",
            "node_collision",
            "dependency_type_mismatch",
            "missing_dependency",
            "config_requirement_missing",
        }


class TestReportObjects:
    def test_problem_attributes(self):
        problem = ValidationProblem("missing_dependency", "x", "x is missing")
        assert problem.category == "missing_dependency"
        assert problem.name == "x"
        assert problem.message == "x is missing"

    def test_problem_unknown_category(self):
        with pytest.raises(PackagingError):
            ValidationProblem("bogus_category", "x", "message")

    def test_problem_non_string_category(self):
        with pytest.raises(PackagingError):
            ValidationProblem(1, "x", "message")

    def test_problem_non_string_name(self):
        with pytest.raises(PackagingError):
            ValidationProblem("missing_dependency", None, "message")

    def test_problem_non_string_message(self):
        with pytest.raises(PackagingError):
            ValidationProblem("missing_dependency", "x", 5)

    def test_report_non_string_package_name(self):
        with pytest.raises(PackagingError):
            ValidationReport(1, [])

    def test_report_non_problem_entries(self):
        with pytest.raises(PackagingError):
            ValidationReport("p", ["oops"])

    def test_report_from_problem_list(self):
        problems = [
            ValidationProblem("missing_dependency", "a", "gone"),
            ValidationProblem("missing_dependency", "b", "gone"),
        ]
        report = ValidationReport("p", problems)
        assert len(report.problems) >= 2
        assert report.is_valid is False

    def test_is_valid_is_boolean(self):
        empty = ValidationReport("p", [])
        assert isinstance(empty.is_valid, bool)
        full = ValidationReport("p", [ValidationProblem("missing_dependency", "x", "x gone")])
        assert isinstance(full.is_valid, bool)

    def test_report_str_contains_problem_messages(self):
        problems = [
            ValidationProblem("missing_dependency", "one", "first thing went missing"),
            ValidationProblem("config_requirement_missing", "two", "second thing is not set"),
        ]
        report = ValidationReport("stringy_pkg", problems)
        rendered = str(report)
        assert "stringy_pkg" in rendered
        assert "first thing went missing" in rendered
        assert "second thing is not set" in rendered

    def test_empty_report_valid(self):
        report = ValidationReport("p", [])
        assert report.is_valid is True
        assert not report.problems


class TestConflictObjects:
    def test_attributes(self):
        conflict = PackageConflict("a", "b", "duplicate_node", "x", "x clashes")
        assert conflict.first_package == "a"
        assert conflict.second_package == "b"
        assert conflict.category == "duplicate_node"
        assert conflict.name == "x"
        assert conflict.message == "x clashes"

    def test_unknown_category(self):
        with pytest.raises(PackagingError):
            PackageConflict("a", "b", "bogus", "x", "message")

    def test_non_string_category(self):
        with pytest.raises(PackagingError):
            PackageConflict("a", "b", 3, "x", "message")

    def test_non_string_name(self):
        with pytest.raises(PackagingError):
            PackageConflict("a", "b", "duplicate_node", 3, "message")

    def test_non_string_package_names(self):
        with pytest.raises(PackagingError):
            PackageConflict(None, "b", "duplicate_node", "x", "message")
        with pytest.raises(PackagingError):
            PackageConflict("a", 4, "duplicate_node", "x", "message")

    def test_str_contains_name(self):
        conflict = PackageConflict("a", "b", "duplicate_node", "x_marks", "x_marks clashes")
        assert "x_marks" in str(conflict)

    def test_categories_constant(self):
        assert set(CONFLICT_CATEGORIES) == {
            "duplicate_node",
            "requirement_mismatch",
            "requirement_disagreement",
        }


class TestFindConflicts:
    def test_first_arg_must_be_package(self):
        with pytest.raises(PackagingError):
            find_conflicts("a", NodePackage("b"))

    def test_second_arg_must_be_package(self):
        with pytest.raises(PackagingError):
            find_conflicts(NodePackage("a"), None)

    def test_disjoint_packages_no_conflicts(self):
        first = NodePackage("a", provides={"x": int})
        second = NodePackage("b", provides={"y": int})
        assert find_conflicts(first, second) == []

    def test_same_name_same_type_no_conflict(self):
        first = NodePackage("a", provides={"x": int})
        second = NodePackage("b", provides={"x": int})
        assert find_conflicts(first, second) == []

    def test_duplicate_node_type_disagreement_both_orders(self):
        first = NodePackage("a", provides={"x": int})
        second = NodePackage("b", provides={"x": str})
        for left, right in [(first, second), (second, first)]:
            conflicts = find_conflicts(left, right)
            found = {(c.category, c.name) for c in conflicts}
            assert ("duplicate_node", "x") in found

    def test_duplicate_node_subtype_still_conflicts(self):
        first = NodePackage("a", provides={"x": bool})
        second = NodePackage("b", provides={"x": int})
        for left, right in [(first, second), (second, first)]:
            found = {(c.category, c.name) for c in find_conflicts(left, right)}
            assert ("duplicate_node", "x") in found

    def test_duplicate_node_dependency_disagreement(self):
        first = NodePackage("a", provides={"x": int, "up": int}, dependencies={"x": ["up"]})
        second = NodePackage("b", provides={"x": int, "up": int}, dependencies={"x": []})
        found = {(c.category, c.name) for c in find_conflicts(first, second)}
        assert ("duplicate_node", "x") in found

    def test_requirement_mismatch_cross_group_both_orders(self):
        provider = NodePackage("a", provides={"x": int})
        requirer = NodePackage("b", requires={"x": bool})
        for left, right in [(provider, requirer), (requirer, provider)]:
            found = {(c.category, c.name) for c in find_conflicts(left, right)}
            assert ("requirement_mismatch", "x") in found

    def test_requirement_satisfied_by_subtype_no_conflict(self):
        provider = NodePackage("a", provides={"x": bool})
        requirer = NodePackage("b", requires={"x": int})
        assert find_conflicts(provider, requirer) == []
        assert find_conflicts(requirer, provider) == []

    def test_generic_alias_conflicts(self):
        provider = NodePackage("a", provides={"x": list[int]})
        matching = NodePackage("b", requires={"x": list[int]})
        assert find_conflicts(provider, matching) == []
        clashing = NodePackage("c", requires={"x": dict[str, int]})
        found = {(c.category, c.name) for c in find_conflicts(provider, clashing)}
        assert ("requirement_mismatch", "x") in found

    def test_any_provider_satisfies_typed_requirer(self):
        provider = NodePackage("a", provides={"x": typing.Any})
        requirer = NodePackage("b", requires={"x": int})
        assert find_conflicts(provider, requirer) == []
        assert find_conflicts(requirer, provider) == []

    def test_any_provider_and_requirer_compatible(self):
        provider = NodePackage("a", provides={"x": typing.Any})
        requirer = NodePackage("b", requires={"x": typing.Any})
        assert find_conflicts(provider, requirer) == []

    def test_requirement_disagreement(self):
        first = NodePackage("a", requires={"x": int})
        second = NodePackage("b", requires={"x": str})
        for left, right in [(first, second), (second, first)]:
            found = {(c.category, c.name) for c in find_conflicts(left, right)}
            assert ("requirement_disagreement", "x") in found

    def test_requirement_agreement_no_conflict(self):
        first = NodePackage("a", requires={"x": int})
        second = NodePackage("b", requires={"x": int})
        assert find_conflicts(first, second) == []

    def test_conflict_attribution(self):
        first = NodePackage("alpha", provides={"x": int})
        second = NodePackage("beta", provides={"x": str})
        conflicts = find_conflicts(first, second)
        for conflict in conflicts:
            assert {conflict.first_package, conflict.second_package} == {"alpha", "beta"}
            assert conflict.name == "x"

    def test_multiple_conflicts_reported(self):
        first = NodePackage("a", provides={"x": int, "y": int}, requires={"z": int})
        second = NodePackage("b", provides={"x": str, "y": str}, requires={"z": str})
        conflicts = find_conflicts(first, second)
        assert len(conflicts) >= 3
        names = {c.name for c in conflicts}
        assert names == {"x", "y", "z"}


class TestComposePackages:
    def test_empty_input_rejected(self):
        with pytest.raises(PackagingError):
            compose_packages([], "combined")

    def test_non_package_entry_rejected(self):
        with pytest.raises(PackagingError):
            compose_packages([NodePackage("a"), 3], "combined")

    def test_bad_name_rejected(self):
        with pytest.raises(PackagingError):
            compose_packages([NodePackage("a")], 7)

    def test_bad_version_rejected(self):
        with pytest.raises(PackagingError):
            compose_packages([NodePackage("a")], "combined", version=0)

    def test_bool_version_rejected(self):
        with pytest.raises(PackagingError):
            compose_packages([NodePackage("a")], "combined", version=True)

    def test_generator_input(self):
        packages = (NodePackage(name, provides={name: int}) for name in ["a", "b"])
        composed = compose_packages(packages, "combined")
        assert set(composed.provides) == {"a", "b"}

    def test_basic_merge(self):
        first = NodePackage(
            "a",
            provides={"x": int},
            requires={"raw": int},
            dependencies={"x": ["raw"]},
            config_keys=["cfg_a"],
        )
        second = NodePackage(
            "b",
            provides={"y": float},
            requires={"x": int},
            dependencies={"y": ["x"]},
            config_keys=["cfg_b"],
        )
        composed = compose_packages([first, second], "combined")
        assert composed.name == "combined"
        assert set(composed.provides) == {"x", "y"}
        assert set(composed.requires) == {"raw"}
        assert set(composed.config_keys) == {"cfg_a", "cfg_b"}
        assert set(composed.dependencies["y"]) == {"x"}
        assert composed.dependency_order().index("x") < composed.dependency_order().index("y")

    def test_config_keys_merge_from_all_members(self):
        first = NodePackage("a", provides={"x": int}, config_keys=["only_a"])
        second = NodePackage("b", provides={"y": int}, config_keys=["only_b", "shared"])
        third = NodePackage("c", provides={"z": int}, config_keys=["shared"])
        composed = compose_packages([first, second, third], "combined")
        assert set(composed.config_keys) == {"only_a", "only_b", "shared"}

    def test_internal_edges_survive_merge(self):
        first = NodePackage(
            "a", provides={"x": int}, requires={"raw": int}, dependencies={"x": ["raw"]}
        )
        second = NodePackage(
            "b", provides={"y": int}, requires={"x": int}, dependencies={"y": ["x"]}
        )
        composed = compose_packages([first, second], "combined")
        assert set(composed.dependencies["x"]) == {"raw"}
        assert set(composed.dependencies["y"]) == {"x"}

    def test_version_defaults_to_max(self):
        first = NodePackage("a", version=2, provides={"x": int})
        second = NodePackage("b", version=5, provides={"y": int})
        assert compose_packages([first, second], "combined").version == 5

    def test_explicit_version_wins(self):
        first = NodePackage("a", version=2)
        assert compose_packages([first], "combined", version=9).version == 9

    def test_same_name_same_type_deduplicated(self):
        first = NodePackage("a", provides={"shared": int, "x": int})
        second = NodePackage("b", provides={"shared": int, "y": int})
        composed = compose_packages([first, second], "combined")
        assert set(composed.provides) == {"shared", "x", "y"}

    def test_internal_satisfaction_honors_subtype(self):
        provider = NodePackage("a", provides={"x": bool})
        requirer = NodePackage(
            "b", provides={"y": int}, requires={"x": int}, dependencies={"y": ["x"]}
        )
        composed = compose_packages([provider, requirer], "combined")
        assert "x" not in composed.requires
        assert set(composed.provides) == {"x", "y"}

    def test_conflict_raises_with_details(self):
        first = NodePackage("a", provides={"clash_point": int})
        second = NodePackage("b", provides={"clash_point": str})
        with pytest.raises(PackageConflictError) as e:
            compose_packages([first, second], "combined")
        assert e.value.conflicts
        for conflict in e.value.conflicts:
            assert isinstance(conflict, PackageConflict)
        assert {conflict.name for conflict in e.value.conflicts} == {"clash_point"}

    def test_conflicting_trio_raises_in_every_order(self):
        first = NodePackage("a", provides={"x": int})
        second = NodePackage("b", requires={"x": bool})
        third = NodePackage("c", provides={"y": int})
        for permutation in itertools.permutations([first, second, third]):
            with pytest.raises(PackageConflictError) as e:
                compose_packages(list(permutation), "combined")
            names = {conflict.name for conflict in e.value.conflicts}
            assert "x" in names

    def test_all_pairs_checked_despite_internal_satisfaction(self):
        provider = NodePackage("a", provides={"x": bool})
        int_requirer = NodePackage("b", requires={"x": int})
        bool_requirer = NodePackage("c", requires={"x": bool})
        for permutation in itertools.permutations([provider, int_requirer, bool_requirer]):
            with pytest.raises(PackageConflictError) as e:
                compose_packages(list(permutation), "combined")
            found = {(conflict.category, conflict.name) for conflict in e.value.conflicts}
            assert ("requirement_disagreement", "x") in found

    def test_order_independent_composition(self):
        first = NodePackage(
            "a",
            version=2,
            provides={"x": int},
            requires={"raw": int},
            dependencies={"x": ["raw"]},
            config_keys=["cfg_a"],
        )
        second = NodePackage(
            "b",
            version=3,
            provides={"y": float},
            requires={"x": int},
            dependencies={"y": ["x"]},
            config_keys=["cfg_b"],
        )
        third = NodePackage(
            "c",
            version=1,
            provides={"z": str},
            requires={"y": float, "other": str},
            dependencies={"z": ["y", "other"]},
            config_keys=["cfg_c"],
        )
        rendered = set()
        for permutation in itertools.permutations([first, second, third]):
            composed = compose_packages(list(permutation), "combined")
            rendered.add(composed.manifest().to_json())
        assert len(rendered) == 1
        composed = compose_packages([first, second, third], "combined")
        assert composed.name == "combined"
        assert composed.version == 3
        assert set(composed.provides) == {"x", "y", "z"}
        assert set(composed.requires) == {"raw", "other"}
        assert set(composed.config_keys) == {"cfg_a", "cfg_b", "cfg_c"}
        assert composed.manifest().to_dict()["provides"]["y"] == htypes.get_type_as_string(float)


class TestManifestDiff:
    def _manifest(self, **overrides):
        kwargs = dict(
            provides={"a": int, "b": float},
            requires={"r": int},
            dependencies={"a": ["r"]},
            config_keys=["cfg"],
        )
        kwargs.update(overrides)
        return NodePackage("p", **kwargs).manifest()

    def test_identical_manifests(self):
        diff = diff_manifests(self._manifest(), self._manifest())
        assert isinstance(diff, ManifestDiff)
        assert diff.has_changes is False
        assert diff.added_nodes == {}
        assert diff.removed_nodes == {}
        assert diff.changed_nodes == {}
        assert diff.added_requirements == {}
        assert diff.removed_requirements == {}
        assert diff.changed_requirements == {}
        assert not diff.added_config_keys
        assert not diff.removed_config_keys

    def test_added_and_removed_nodes(self):
        old = self._manifest()
        new = self._manifest(provides={"a": int, "c": str}, dependencies={"a": ["r"]})
        diff = diff_manifests(old, new)
        assert set(diff.added_nodes) == {"c"}
        assert diff.added_nodes["c"] == htypes.get_type_as_string(str)
        assert set(diff.removed_nodes) == {"b"}
        assert diff.has_changes is True

    def test_changed_node_type(self):
        old = self._manifest()
        new = self._manifest(provides={"a": str, "b": float})
        diff = diff_manifests(old, new)
        assert diff.changed_nodes["a"] == (
            htypes.get_type_as_string(int),
            htypes.get_type_as_string(str),
        )

    def test_requirement_changes(self):
        old = self._manifest()
        new = self._manifest(requires={"r": float, "s": int}, dependencies={"a": ["r"]})
        diff = diff_manifests(old, new)
        assert set(diff.added_requirements) == {"s"}
        assert diff.changed_requirements["r"] == (
            htypes.get_type_as_string(int),
            htypes.get_type_as_string(float),
        )
        removed = diff_manifests(new, old)
        assert set(removed.removed_requirements) == {"s"}

    def test_config_key_changes(self):
        old = self._manifest()
        new = self._manifest(config_keys=["other"], dependencies={"a": ["r"]})
        diff = diff_manifests(old, new)
        assert set(diff.added_config_keys) == {"other"}
        assert set(diff.removed_config_keys) == {"cfg"}

    def test_has_changes_is_boolean(self):
        same = diff_manifests(self._manifest(), self._manifest())
        assert isinstance(same.has_changes, bool)
        different = diff_manifests(self._manifest(), self._manifest(config_keys=[]))
        assert isinstance(different.has_changes, bool)
        assert different.has_changes is True

    def test_rejects_non_manifests(self):
        with pytest.raises(PackagingError):
            diff_manifests({"name": "p"}, self._manifest())
        with pytest.raises(PackagingError):
            diff_manifests(self._manifest(), None)

    def test_constructor_matches_function(self):
        old = self._manifest()
        new = self._manifest(provides={"a": int, "c": str}, dependencies={"a": ["r"]})
        assert ManifestDiff(old, new).added_nodes == diff_manifests(old, new).added_nodes


class TestExceptions:
    def test_hierarchy(self):
        assert issubclass(PackageValidationError, PackagingError)
        assert issubclass(PackageConflictError, PackagingError)
        assert issubclass(PackagingError, Exception)

    def test_validation_error_requires_report(self):
        with pytest.raises(PackagingError):
            PackageValidationError("not a report")

    def test_validation_error_rejects_valid_report(self):
        with pytest.raises(PackagingError):
            PackageValidationError(ValidationReport("p", []))

    def test_validation_error_carries_report_and_messages(self):
        problems = [
            ValidationProblem("missing_dependency", "gone_one", "gone_one is not available"),
            ValidationProblem("config_requirement_missing", "gone_two", "gone_two is not set"),
        ]
        report = ValidationReport("p", problems)
        error = PackageValidationError(report)
        assert error.report is report
        assert "gone_one is not available" in str(error)
        assert "gone_two is not set" in str(error)

    def test_conflict_error_requires_conflicts(self):
        with pytest.raises(PackagingError):
            PackageConflictError([])

    def test_conflict_error_rejects_non_conflicts(self):
        with pytest.raises(PackagingError):
            PackageConflictError(["oops"])

    def test_validation_error_repr_mentions_report(self):
        report = ValidationReport(
            "repr_err_pkg",
            [ValidationProblem("missing_dependency", "gone_dep", "gone_dep missing")],
        )
        rendered = repr(PackageValidationError(report))
        assert "repr_err_pkg" in rendered
        assert "gone_dep" in rendered

    def test_conflict_error_repr_mentions_conflict(self):
        conflict = PackageConflict("a", "b", "duplicate_node", "clash_here", "clash_here twice")
        rendered = repr(PackageConflictError([conflict]))
        assert "clash_here" in rendered

    def test_conflict_error_carries_conflicts_and_messages(self):
        conflicts = [
            PackageConflict("a", "b", "duplicate_node", "x", "x provided twice"),
            PackageConflict("a", "b", "requirement_disagreement", "y", "y expected differently"),
        ]
        error = PackageConflictError(conflicts)
        assert list(error.conflicts) == conflicts
        assert "x provided twice" in str(error)
        assert "y expected differently" in str(error)


class TestDriverIntegration:
    def test_with_packages_rejects_non_package(self):
        with pytest.raises(ValueError):
            driver.Builder().with_packages("not a package")

    def test_with_packages_rejects_falsey_non_packages(self):
        with pytest.raises(ValueError):
            driver.Builder().with_packages(None)
        with pytest.raises(ValueError):
            driver.Builder().with_packages(0)

    def test_with_packages_rejects_sequence(self):
        packages = [NodePackage("a"), NodePackage("b")]
        with pytest.raises(ValueError):
            driver.Builder().with_packages(packages)

    def test_build_with_compatible_package(self):
        module = ad_hoc_utils.create_temporary_module(base_int, doubled)
        package = NodePackage("p", requires={"base_int": int})
        dr = driver.Builder().with_modules(module).with_packages(package).build()
        assert dr.list_packages() == [package]
        reports = dr.validate_packages()
        assert len(reports) == 1
        assert reports[0].is_valid is True
        assert reports[0].package_name == "p"

    def test_build_failure_carries_report(self):
        module = ad_hoc_utils.create_temporary_module(base_int)
        package = NodePackage("p", requires={"long_gone": int})
        with pytest.raises(PackageValidationError) as e:
            driver.Builder().with_modules(module).with_packages(package).build()
        assert isinstance(e.value.report, ValidationReport)
        by_name = {problem.name: problem for problem in e.value.report.problems}
        assert by_name["long_gone"].category == "missing_dependency"
        for problem in e.value.report.problems:
            assert problem.message in str(e.value)

    def test_build_failure_multiple_problems_in_message(self):
        module = ad_hoc_utils.create_temporary_module(base_int)
        package = NodePackage(
            "p", requires={"gone_one": int, "gone_two": int}, config_keys=["gone_key"]
        )
        with pytest.raises(PackageValidationError) as e:
            driver.Builder().with_modules(module).with_packages(package).build()
        assert len(e.value.report.problems) >= 3
        assert {problem.name for problem in e.value.report.problems} == {
            "gone_one",
            "gone_two",
            "gone_key",
        }
        for problem in e.value.report.problems:
            assert problem.message in str(e.value)

    def test_async_build_failure_carries_report(self):
        module = ad_hoc_utils.create_temporary_module(base_int)
        package = NodePackage("p", requires={"long_gone": int})
        builder = async_driver.Builder().with_modules(module).with_packages(package)
        with pytest.raises(PackageValidationError) as e:
            builder.build_without_init()
        assert isinstance(e.value.report, ValidationReport)
        assert {problem.name for problem in e.value.report.problems} == {"long_gone"}

    def test_async_build_success_keeps_packages(self):
        module = ad_hoc_utils.create_temporary_module(base_int)
        package = NodePackage("p", requires={"base_int": int})
        dr = async_driver.Builder().with_modules(module).with_packages(package).build_without_init()
        assert dr.list_packages() == [package]

    def test_no_packages_by_default(self):
        module = ad_hoc_utils.create_temporary_module(base_int)
        dr = driver.Builder().with_modules(module).build()
        assert dr.list_packages() == []
        assert dr.validate_packages() == []

    def test_with_packages_accumulates(self):
        first = NodePackage("a", requires={"base_int": int})
        second = NodePackage("b", requires={"doubled": int})
        module = ad_hoc_utils.create_temporary_module(base_int, doubled)
        dr = (
            driver.Builder().with_modules(module).with_packages(first).with_packages(second).build()
        )
        assert {p.name for p in dr.list_packages()} == {"a", "b"}
        assert {r.package_name for r in dr.validate_packages()} == {"a", "b"}

    def test_with_packages_accepts_varargs_in_one_call(self):
        first = NodePackage("a", requires={"base_int": int})
        second = NodePackage("b", requires={"doubled": int})
        module = ad_hoc_utils.create_temporary_module(base_int, doubled)
        dr = driver.Builder().with_modules(module).with_packages(first, second).build()
        assert {p.name for p in dr.list_packages()} == {"a", "b"}
        assert all(report.is_valid for report in dr.validate_packages())

    def test_builder_copy_preserves_packages(self):
        module = ad_hoc_utils.create_temporary_module(base_int)
        package = NodePackage("p", requires={"base_int": int})
        builder = (
            driver.Builder().with_modules(module).with_config({"someone": 1}).with_packages(package)
        )
        copied = builder.copy()
        assert copied.config == builder.config
        assert copied.modules == builder.modules
        builder.with_packages(NodePackage("later"))
        builder.with_config({"added_later": 2})
        builder.with_modules(ad_hoc_utils.create_temporary_module(doubled))
        assert "added_later" not in copied.config
        assert len(copied.modules) == 1
        dr = copied.build()
        assert dr.list_packages() == [package]

    def test_multiple_modules_supply_requirements(self):
        first_module = ad_hoc_utils.create_temporary_module(base_int, module_name="pkg_mod_a")
        second_module = ad_hoc_utils.create_temporary_module(
            doubled, as_float, module_name="pkg_mod_b"
        )
        package = NodePackage("p", requires={"base_int": int, "as_float": float})
        dr = (
            driver.Builder()
            .with_modules(first_module, second_module)
            .with_packages(package)
            .build()
        )
        assert dr.validate_packages()[0].is_valid is True

    def test_config_satisfied_package_through_builder(self):
        module = ad_hoc_utils.create_temporary_module(base_int, scaled)
        package = NodePackage("p", requires={"factor": int}, config_keys=["factor"])
        dr = (
            driver.Builder()
            .with_modules(module)
            .with_config({"factor": 2})
            .with_packages(package)
            .build()
        )
        assert dr.validate_packages()[0].is_valid is True

    def test_manifest_fields_constant(self):
        assert set(MANIFEST_FIELDS) == {
            "name",
            "version",
            "provides",
            "requires",
            "dependencies",
            "config_keys",
        }

    def test_packaged_subgraph_round_trip_through_export(self, tmp_path):
        dr = _build_driver(base_int, doubled, as_float)
        package = NodePackage.from_graph(dr.graph, ["doubled", "as_float"], "p", version=2)
        path = tmp_path / "p.json"
        export_package(package, path)
        manifest = import_manifest(path)
        data = manifest.to_dict()
        assert data["version"] == 2
        assert set(data["provides"]) == {"doubled", "as_float"}
        assert data["provides"]["doubled"] == htypes.get_type_as_string(int)
        assert manifest.dependency_order() == package.dependency_order()


class TestRemainingSurface:
    def test_include_upstream_skips_optional_and_config_dependencies(self):
        dr = _build_driver(base_int, scaled, with_default, config={"factor": 2})
        package = NodePackage.from_graph(
            dr.graph, ["scaled", "with_default"], "p", include_upstream=True
        )
        assert set(package.provides) == {"base_int", "scaled", "with_default"}
        assert set(package.config_keys) == {"factor"}
        assert not package.requires

    def test_reprs_mention_identifying_fields(self):
        package = _simple_package("repr_pkg")
        assert "repr_pkg" in repr(package)
        assert "repr_pkg" in repr(package.manifest())
        problem = ValidationProblem("missing_dependency", "repr_name", "repr_name gone")
        assert "repr_name" in repr(problem)
        report = ValidationReport("repr_pkg", [problem])
        assert "repr_pkg" in repr(report)
        conflict = PackageConflict("a", "b", "duplicate_node", "repr_name", "repr_name clashes")
        assert "repr_name" in repr(conflict)
