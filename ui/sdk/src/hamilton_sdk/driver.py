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

import datetime
import hashlib
import inspect
import json
import logging
import operator
import os
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from hamilton_sdk.api.clients import UnauthorizedException

from hamilton import base, driver, graph, node
from hamilton.driver import Variable
from hamilton.io import materialization
from hamilton.lifecycle.base import BaseDoNodeExecute
from hamilton.node import Node

try:
    import git
except ImportError:
    git = None

from hamilton_sdk.api import clients, constants
from hamilton_sdk.api.projecttypes import GitInfo
from hamilton_sdk.tracking.runs import Status, TrackingState, monkey_patch_adapter

logger = logging.getLogger(__name__)


def _hash_module(
    module: ModuleType, hash_object: hashlib.sha256, seen_modules: Set[ModuleType]
) -> hashlib.sha256:
    """Generate a hash of the specified module and its imports.

    It will recursively hash the contents of the modules and their imports, and only does so
    if the import is from the same package. This is to avoid hashing the entire python
    environment...

    :param module: the python module to hash and then crawl.
    :param hash_object: the object to update.
    :param seen_modules: the python modules we've already hashed.
    :return: the updated hash object
    """
    # Check if we've already hashed this module
    if module in seen_modules:
        return hash_object
    else:
        seen_modules.add(module)
    # Update the hash with the module's source code
    if hasattr(module, "__file__") and module.__file__ is not None:
        with open(module.__file__, "rb") as f:
            hash_object.update(f.read())
    else:
        logger.debug(
            "Skipping hash for module %s because it has no __file__ attribute or it is None.",
            module,
        )

    def safe_getmembers(module):
        """Need this because some modules are lazily loaded and we can't get the members.
        e.g. ibis.
        """
        try:
            return inspect.getmembers(module)
        except Exception as e:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    f"Skipping hash for module {module.__name__} because we could not get the members. "
                    f"Error: {e}"
                )
            return []

    # Loop through the module's attributes
    for name, value in safe_getmembers(module):
        # Check if the attribute is a module
        if inspect.ismodule(value):
            if value.__package__ is None:
                logger.info(
                    f"Skipping hash for module {value.__name__} because it has no __package__ "
                    f"attribute or it is None. This happens with lazy loaders."
                )
                continue
            # Check if the module is in the same top level package
            if (
                value.__package__ != module.__package__
                and module.__package__ is not None
                and not value.__package__.startswith(module.__package__)
            ):
                logger.debug(
                    f"Skipping hash for module {value.__name__} because it is in a different "
                    f"package {value.__package__} than {module.__package__}"
                )
                continue
            # Recursively hash the sub-module
            hash_object = _hash_module(value, hash_object, seen_modules)

    # Return the hash object
    return hash_object


def _get_modules_hash(modules: Tuple[ModuleType]) -> str:
    """Generate a hash of the contents of the specified modules.

    It recursively hashes the contents of the modules and their imports, and only does so
    if the import is from the same package. This is to avoid hashing the entire python
    environment...

    :param modules: python modules to hash
    :return: the hex digest of the hash
    """
    # Create a hash object
    h = hashlib.sha256()
    seen_modules = set()

    # Loop through each module name
    for module in modules:
        # Update the hash with the module's source code
        h = _hash_module(module, h, seen_modules)

    # Return the hex digest of the hash
    return h.hexdigest()


def _derive_version_control_info(module_hash: str) -> GitInfo:
    """Derive the git info for the current project.
    Currently, this decides whether we're in a git repository.
    This is not going to work for everything, but we'll see what the customers want.
    We might end up having to pass this data in...
    """
    default = GitInfo(
        branch="unknown",
        commit_hash=module_hash,
        committed=False,
        repository="Error: No repository to link to.",
        local_repo_base_path=os.getcwd(),
    )
    if git is None:
        return default
    try:
        repo = git.Repo(".", search_parent_directories=True)
    except git.exc.InvalidGitRepositoryError:
        logger.warning(
            "Warning: We are not currently in a git repository. We recommend using that as a "
            "way to version the "
            "project *if* your hamilton code lives within this repository too. If it does not,"
            " then we'll try to "
            "version code based on the python modules passed to the Driver. "
            "Incase you want to get set up with git quickly you can run:\n "
            "git init && git add . && git commit -m 'Initial commit'\n"
            "Still have questions? Reach out to stefan @ dagworks.io, elijah @ dagworks.io "
            "and we'll try to help you as soon as possible."
        )
        return default
    if "COLAB_RELEASE_TAG" in os.environ:
        logger.warning(
            "We currently do not support logging version information inside a google"
            "colab notebook. This is something we are planning to do. "
            "If you have any questions, please reach out to support@dagworks.io"
            "and we'll try to help you as soon as possible."
        )
        return default

    try:
        commit = repo.head.commit
    except Exception:
        return default
    try:
        repo_url = repo.remote().url
    except Exception:
        # TODO: change this to point to our docs on what to do.
        repo_url = "Error: No repository to link to."
    try:
        branch_name = repo.active_branch.name
    except Exception:
        branch_name = "unknown"  # detached head
        logger.warning(
            "Warning: we are unable to determine the branch name. "
            "This is likely because you are in a detached head state. "
            "If you are in a detached head state, you can check out a "
            "branch by running `git checkout -b <branch_name>`. "
            "If you intend to be (if you are using some sort of CI"
            "system that checks out a detached head) then you can ignore this."
        )
    return GitInfo(
        branch=branch_name,
        commit_hash=commit.hexsha,
        committed=not repo.is_dirty(),
        repository=repo_url,
        local_repo_base_path=repo.working_dir,
    )


def filter_json_dict_to_serializable(
    dict_to_filter: Dict[str, Any], curr_result: Dict[str, Any] = None
):
    if curr_result is None:
        curr_result = {}
    if dict_to_filter is None:
        dict_to_filter = {}
    for key, value in dict_to_filter.items():
        try:
            json.dumps(value)
            curr_result[key] = value
        except TypeError:
            if isinstance(value, dict):
                new_result = {}
                filter_json_dict_to_serializable(value, new_result)
                curr_result[key] = new_result
            else:
                curr_result[key] = str(value)
    return curr_result


def validate_tags(tags: Any):
    """Validates that tags are a dictionary of strings to strings.

    :param tags: Tags to validate
    :raises ValueError: If tags are not a dictionary of strings to strings
    """
    if not isinstance(tags, dict):
        raise ValueError(f"Tags must be a dictionary, but got {tags}")
    for key, value in tags.items():
        if not isinstance(key, str):
            raise ValueError(f"Tag keys must be strings, but got {key}")
        if not isinstance(value, str):
            raise ValueError(f"Tag values must be strings, but got {value}")


def safe_len(x):
    return len(x) if x is not None else 0


# Placeholder so we can monkey-patch later (see monkey_patch_adapter)
class DefaultExecutionMethod(BaseDoNodeExecute):
    def do_node_execute(
        self,
        *,
        run_id: str,
        node_: node.Node,
        kwargs: Dict[str, Any],
        task_id: Optional[str] = None,
    ) -> Any:
        return node_(**kwargs)


class Driver(driver.Driver):
    def __init__(
        self,
        config: Dict[str, Any],
        *modules: ModuleType,
        project_id: int,
        api_key: str,
        username: str,
        dag_name: str,
        tags: Dict[str, str] = None,
        client_factory: Callable[
            [str, str, str], clients.HamiltonClient
        ] = clients.BasicSynchronousHamiltonClient,
        adapter: base.HamiltonGraphAdapter = None,
        dagworks_api_url=os.environ.get("DAGWORKS_API_URL", constants.HAMILTON_API_URL),
        dagworks_ui_url=os.environ.get("DAGWORKS_UI_URL", constants.HAMILTON_UI_URL),
    ):
        """Instantiates a DAGWorks driver. This:
        1. Requires a project to exist. Create one via https://app.dagworks.io/dashboard/projects.
        2. Sends over the shape of the DAG.
        3. Sets up execute() run-tracking.

        :param config: Configuration to use, same as standard Hamilton driver.
        :param modules: Modules to use, same as standard Hamilton driver.
        :param project_id: Identifier for the project to use to store this DAG under.
        :param api_key: API key to use for authentication. Remember not to save this in plaintext!
        :param username: username for authentication.
        :param dag_name: name for this DAG. You will use this for top level curation of DAGs
        within a project.
        :param tags: Optional key value string pairs to help identify and curate this instance of
        the DAG and subsequent execution runs. E.g. {"environment": "production"}.
        Currently all .execute() runs will be tagged with these.
        :param client_factory: Optional. Advanced use. Factory to use to create the underlying
        client.
        :param adapter: Optional. Adapter to use, same as standard Hamilton driver.
        :param dagworks_api_url: Optional. URL to use for the DAGWorks API.
        :param dagworks_ui_url: Optional. URL to use for the DAGWorks UI.
        """
        if adapter is None:
            adapter = base.SimplePythonGraphAdapter(result_builder=base.DictResult())
        super(Driver, self).__init__(config, *modules, adapter=adapter)

        self.config = config
        self.project = project_id
        self.api_key = api_key
        self.username = username
        # TODO -- figure out how to pass any additional configuration to the client if needed
        self.client = client_factory(api_key, username, dagworks_api_url)
        self.module_hash = _get_modules_hash(modules)
        self.vcs_info = _derive_version_control_info(self.module_hash)
        self.initialized = False
        self.modules = modules
        self.project_version = None
        self.run_tags = tags if tags is not None else {}
        validate_tags(self.run_tags)
        self.dag_name = dag_name
        self.dagworks_ui_url = dagworks_ui_url
        # reassign the graph executor with all the information we have
        self.graph_executor = DAGWorksGraphExecutor(
            self.graph_executor,
            self.client,
            self.run_tags,
            self.dagworks_ui_url,
            self.project,
            self.vcs_info.local_repo_base_path,
            self.vcs_info,
            self.dag_name,
            list(self.graph_modules),
            self.graph,
        )
        self.initialize()

    def set_name(self, new_name: str):
        """Sets a name for the driver. This allows you to force a change in the name/version of the
        DAG so the next run logs a new one.

        :param new_name:
        """
        self.dag_name = new_name
        self.graph_executor.dag_name = new_name

    def initialize(self):
        """Initializes the driver. This:
        1. Validates authentication
        2. Creates a project if it does not already exist
        3. Sets initialization as true

        Note this is idempotent -- it can be called by the user to test, but will get called when
        the driver runs.

        """
        logger.debug("Validating authentication against DAGWorks API...")
        self.client.validate_auth()
        logger.debug("Authentication successful!")
        logger.debug(f"Ensuring project {self.project} exists...")
        try:
            exists = self.client.project_exists(self.project)
        except UnauthorizedException:
            logger.exception(
                f"Authentication failed. Please check your credentials and try again. "
                f"Username: {self.username}, API key: {self.api_key[0:6]}..."
            )
            raise
        if not exists:
            logger.error(
                f"Project {self.project} does not exist. Please create it first in the UI! "
                f"You can do so at https://www.app.dagworks.io/dashboard/projects"
            )
        self.graph_executor.initialize()
        self.initialized = True

    def execute(
        self,
        final_vars: List[Union[str, Callable]],
        overrides: Dict[str, Any] = None,
        display_graph: bool = False,
        inputs: Dict[str, Any] = None,
    ) -> Any:
        logger.warning(
            f"\nCapturing execution run. All runs for project can be found at "
            f"{self.dagworks_ui_url}/dashboard/project/{self.project}/runs"
        )
        return super(Driver, self).execute(final_vars, overrides, display_graph, inputs)

    def raw_execute(
        self,
        final_vars: List[str],
        overrides: Dict[str, Any] = None,
        display_graph: bool = False,
        inputs: Dict[str, Any] = None,
        _fn_graph: graph.FunctionGraph = None,
    ) -> Dict[str, Any]:
        return super(Driver, self).raw_execute(
            final_vars, overrides, display_graph, inputs, _fn_graph
        )

    def materialize(
        self,
        *materializers: materialization.MaterializerFactory,
        additional_vars: List[Union[str, Callable, Variable]] = None,
        overrides: Dict[str, Any] = None,
        inputs: Dict[str, Any] = None,
    ) -> Tuple[Any, Dict[str, Any]]:
        return super(Driver, self).materialize(
            *materializers, additional_vars=additional_vars, overrides=overrides, inputs=inputs
        )


def _get_fully_qualified_function_path(fn: Callable) -> str:
    """Gets the fully qualified path of a function.

    :param fn: Function to get the path of
    :return: Fully qualified path of the function
    """
    module = inspect.getmodule(fn)
    fn_name = fn.__name__
    if module is not None:
        fn_name = f"{module.__name__}.{fn_name}"
    return fn_name


def hash_dag(dag: graph.FunctionGraph) -> str:
    """Hashes a DAG.

    :param dag: DAG to hash
    :return: Hash of the DAG
    """
    digest = hashlib.sha256()

    hashing_node_fields = {
        "name": str,
        "type": str,  # Hash it to a string for the type
        "node_role": str,
        "dependencies": lambda x: " ".join(
            [item.name for item in sorted(x, key=operator.attrgetter("name"))]
        ),  # Sort dependencies
    }

    for node_ in sorted(dag.nodes.values(), key=operator.attrgetter("name")):
        for field, serializer in hashing_node_fields.items():
            digest.update(json.dumps(serializer(getattr(node_, field))).encode())
        if node_.originating_functions is None:
            continue
        for fn in node_.originating_functions:
            fn_name = _get_fully_qualified_function_path(fn)
            digest.update(fn_name.encode())
    return digest.hexdigest()


def hash_dag_modules(dag: graph.FunctionGraph, modules: List[ModuleType]):
    modules_by_path = {}
    for module in modules:
        if hasattr(module, "__file__") and module.__file__ is not None:
            try:
                modules_by_path[module.__file__] = inspect.getsource(module)
            except OSError:
                logger.warning(
                    f"Skipping hashing of module {module.__name__} because we could not read the source code."
                )
    digest = hashlib.sha256()
    for node_ in sorted(dag.nodes.values(), key=operator.attrgetter("name")):
        if node_.originating_functions is None:
            continue
        for fn in node_.originating_functions:
            module = inspect.getmodule(fn)
            if hasattr(module, "__file__") and module.__file__ is not None:
                modules_by_path[module.__file__] = module
    for module_path, module_contents in sorted(modules_by_path.items()):
        # if the filename is tmpXXXXXXXX.py  assume it's a temporary file and skip hashing the name
        # this could be in a jupyter context in which case this will cause different code
        # versions when in fact there are none.
        file_name = os.path.basename(module_path)
        if file_name.startswith("tmp") and len(file_name) == 14:
            pass
        else:
            digest.update(module_path.encode())
        digest.update(_get_modules_hash((module_contents,)).encode())
    return digest.hexdigest()


def _convert_node_dependencies(node: Node) -> dict:
    dependencies = []
    dependency_specs = []
    dependency_specs_type = "python_type"
    dependency_specs_schema_version = 1
    for node_ in node.dependencies:
        dependencies.append(node_.name)
        dependency_specs.append({"type_name": str(node_.type)})

    return {
        "dependencies": dependencies,
        "dependency_specs": dependency_specs,
        "dependency_specs_type": dependency_specs_type,
        "dependency_specs_schema_version": dependency_specs_schema_version,
    }


def _convert_classifications(node_: Node) -> List[str]:
    out = []
    if (
        node_.tags.get("hamilton.data_loader")
        and node_.tags.get("hamilton.data_loader.has_metadata") is not False
    ):
        out.append("data_loader")
    elif node_.tags.get("hamilton.data_saver"):
        out.append("data_saver")
    elif node_.user_defined:
        out.append("input")
    else:
        out.append("transform")
    return out


def _extract_node_templates_from_function_graph(fn_graph: graph.FunctionGraph) -> List[dict]:
    """Converts a function graph to a list of nodes that the DAGWorks graph can understand.

    @param fn: Function graph to convert
    @return: A list of node objects
    """
    node_templates = []
    for node_ in fn_graph.nodes.values():
        code_artifact_pointers = (
            []
            if (node_.originating_functions is None or len(node_.originating_functions) == 0)
            else [_get_fully_qualified_function_path(fn) for fn in node_.originating_functions]
        )
        node_templates.append(
            dict(
                name=node_.name,
                output={"type_name": str(node_.type)},
                output_type="python_type",
                output_schema_version=1,  # TODO -- merge this with _convert_node_dependencies
                documentation=node_.documentation,
                tags=node_.tags,  # TODO -- ensure serializable
                classifications=_convert_classifications(node_),  # TODO -- manage classifications
                code_artifact_pointers=(
                    code_artifact_pointers
                    if node_.originating_functions is None or len(node_.originating_functions) == 0
                    else [
                        _get_fully_qualified_function_path(fn) for fn in node_.originating_functions
                    ]
                ),
                **_convert_node_dependencies(node_),
            )
        )
    return node_templates


def _derive_url(vcs_info: GitInfo, path: str, line: int) -> str:
    """Derives a URL from a VCS info, a path, and a line number.

    @param vcs_info: VCS info
    @param path: Path
    @param line: Line number
    @return: A URL
    """
    if vcs_info.repository == "Error: No repository to link to.":
        return "Error: No repository to link to."
    if vcs_info.repository.endswith(".git"):
        repo_url = vcs_info.repository[:-4]
    else:
        repo_url = vcs_info.repository
    return f"{repo_url}/blob/{vcs_info.commit_hash}/{path}#L{line}"


def getsourcelines(object, stop: Callable = None) -> tuple:
    """Adding this here incase we want to pull decorator code too.

    This is modification of the underlying inspect function.

    Return a list of source lines and starting line number for an object.
    The argument may be a module, class, method, function, traceback, frame,
    or code object.  The source code is returned as a list of the lines
    corresponding to the object and the line number indicates where in the
    original source file the first line of code was found.  An OSError is
    raised if the source code cannot be retrieved.

    This will return the decorator code, or the underlying wrapped function code.
    """
    object = inspect.unwrap(object, stop=stop)
    lines, lnum = inspect.findsource(object)
    if inspect.istraceback(object):
        object = object.tb_frame
    # for module or frame that corresponds to module, return all source lines
    if inspect.ismodule(object) or (
        inspect.isframe(object) and object.f_code.co_name == "<module>"
    ):
        return lines, 0
    else:
        return inspect.getblock(lines[lnum:]), lnum + 1


def extract_code_artifacts_from_function_graph(
    fn_graph: graph.FunctionGraph, vcs_info: GitInfo, repo_base_path: str
) -> List[dict]:
    """Converts a function graph to a list of code artifacts that the function graph uses.

    @param fn_graph: Function graph to convert.
    @return: A list of node objects.
    """
    seen = set()
    out = []
    for node_ in fn_graph.nodes.values():
        originating_functions = node_.originating_functions
        if originating_functions is None:
            continue
        for fn in originating_functions:
            fn_name = _get_fully_qualified_function_path(fn)
            if fn_name not in seen:
                seen.add(fn_name)
                # need to handle decorators -- they will return the wrong sourcefile.
                unwrapped_fn = inspect.unwrap(fn)
                if unwrapped_fn != fn:
                    # TODO: pull decorator stuff too
                    source_file = inspect.getsourcefile(unwrapped_fn)
                else:
                    source_file = inspect.getsourcefile(fn)
                if source_file is not None:
                    path = os.path.relpath(source_file, repo_base_path)
                else:
                    path = ""
                try:
                    source_lines = inspect.getsourcelines(fn)
                    out.append(
                        dict(
                            name=fn_name,
                            type="p_function",
                            path=path,
                            start=inspect.getsourcelines(fn)[1] - 1,
                            end=inspect.getsourcelines(fn)[1] - 1 + len(source_lines[0]),
                            url=_derive_url(vcs_info, path, source_lines[1]),
                        )
                    )
                except OSError:
                    # This is an error state where somehow we don't have
                    # source code.
                    out.append(
                        dict(
                            name=fn_name,
                            type="p_function",
                            path=path,
                            start=0,
                            end=0,
                            url=_derive_url(vcs_info, path, 0),
                        )
                    )
    return out


def extract_attributes_from_tracking_state(tracking_state: TrackingState) -> List[dict]:
    """Extracts attributes from tracking state. We'll likely rewrite this shortly --
    this is just to bridge so we can get the client out. Next, we'll want it putting
    stuff on a queue, and then sends it over in batches. The tracking state is a hack
    and we'll get rid of it.

    @param tracking_state: Tracking state
    @return: A list of attributes
    """
    # This just bridges some of the old code so we can move quickly
    # TODO -- fix so we don't have to do that
    out = []
    dag_run = tracking_state.get()
    for task in dag_run.tasks:
        if task.error is not None:
            out.append(
                dict(
                    node_name=task.node_name,
                    name="stack_trace",
                    type="error",
                    schema_version=1,
                    value={
                        "stack_trace": task.error,
                    },
                    attribute_role="error",
                )
            )
        if task.result_summary is not None:
            out.append(
                dict(
                    node_name=task.node_name,
                    name="result_summary",
                    type=task.result_summary["observability_type"],
                    # 0.0.3 -> 3
                    schema_version=int(
                        task.result_summary["observability_schema_version"].split(".")[-1]
                    ),
                    value=task.result_summary["observability_value"],
                    attribute_role="result_summary",
                )
            )
    return out


def extract_task_updates_from_tracking_state(
    tracking_state: TrackingState, fg: graph.FunctionGraph
) -> List[dict]:
    """Extracts task updates from tracking state. We'll likely rewrite this shortly --
    this is a hack (using the tracking state) -- we'll want to extract these as we go along,
    and we'll want it putting stuff on a queue, and then sends it over in batches.

    @param tracking_state:
    @return:
    """
    # TODO -- do the tracking state in a cleaner way
    # This is left over from the old way we were doing things
    dag_run = tracking_state.get()
    out = []
    for task in dag_run.tasks:
        node_ = fg.nodes[task.node_name]
        out.append(
            dict(
                node_template_name=task.node_name,
                node_name=task.node_name,
                realized_dependencies=[dep.name for dep in node_.dependencies],
                status=task.status,
                start_time=task.start_time,
                end_time=task.end_time,
            )
        )
    return out


def _slurp_code(fg: graph.FunctionGraph, repo_base: str) -> List[dict]:
    modules = set()
    for node_ in fg.nodes.values():
        originating_functions = node_.originating_functions
        if originating_functions is None:
            continue
        for fn in originating_functions:
            module = inspect.getmodule(fn)
            modules.add(module)
    out = []
    for module in modules:
        if hasattr(module, "__file__") and module.__file__ is not None:
            module_path = os.path.relpath(module.__file__, repo_base)
            with open(module.__file__, "r") as f:
                out.append({"path": module_path, "contents": f.read()})
    return out


class DAGWorksGraphExecutor(driver.GraphExecutor):
    def __init__(
        self,
        wrapping_executor: driver.GraphExecutor,
        client: clients.HamiltonClient,
        run_tags: Dict[str, str],
        dagworks_ui_url: str,
        project_id: int,
        repo_base: str,
        vcs_info: GitInfo,
        dag_name: str,
        graph_modules: List[ModuleType],
        initial_graph: graph.FunctionGraph,
    ):
        self.executor = wrapping_executor
        self.client = client
        self.run_tags = run_tags
        self.dagworks_ui_url = dagworks_ui_url
        self.project_id = project_id
        self.repo_base = repo_base
        self.vcs_info = vcs_info
        self.dag_name = dag_name
        self.graph_modules = graph_modules
        self.dag_template_id_cache = {}
        self.initial_graph = initial_graph

    def initialize(self):
        self._register_or_query(self.initial_graph)

    def _register_or_query(self, fg: graph.FunctionGraph) -> int:
        """Creates a DAG template if the funtion graph doesn't exist. Otherwise
        we use the cache we see. Note that if this already

        @param fg:
        @return:
        """
        # Quick way to bypass anything complicated
        fg_id = id(fg)
        if fg_id in self.dag_template_id_cache:
            return self.dag_template_id_cache[fg_id]
        dag_hash = hash_dag(fg)
        code_hash = hash_dag_modules(fg, self.graph_modules)
        dag_template_id = self.client.register_dag_template_if_not_exists(
            project_id=self.project_id,
            dag_hash=dag_hash,
            code_hash=code_hash,
            name=self.dag_name,
            nodes=_extract_node_templates_from_function_graph(fg),
            code_artifacts=extract_code_artifacts_from_function_graph(
                fg, self.vcs_info, self.repo_base
            ),
            config=fg.config,
            tags=self.run_tags,
            code=_slurp_code(fg, self.repo_base),
            vcs_info=self.vcs_info,
        )
        self.dag_template_id_cache[fg_id] = dag_template_id
        return dag_template_id

    def execute(
        self,
        fg: graph.FunctionGraph,
        final_vars: List[Union[str, Callable, Variable]],
        overrides: Dict[str, Any],
        inputs: Dict[str, Any],
        run_id: str,
    ) -> Dict[str, Any]:
        """Executes a graph in a blocking function.

        :param fg: Graph to execute
        :param final_vars: Variables we want
        :param overrides: Overrides --- these short-circuit computation
        :param inputs: Inputs to the Graph.
        :return: The output of the final variables, in dictionary form.
        """
        logger.info(f"Logging code version for DAG {self.dag_name}...")
        dag_template_id = self._register_or_query(fg)
        tracking_state = TrackingState(run_id)
        with monkey_patch_adapter(fg.adapter, tracking_state):
            tracking_state.clock_start()
            dag_run_id = self.client.create_and_start_dag_run(
                dag_template_id=dag_template_id,
                tags=self.run_tags,
                inputs=inputs if inputs is not None else {},
                outputs=final_vars,
            )
            try:
                out = self.executor.execute(fg, final_vars, overrides, inputs, run_id=dag_run_id)
                tracking_state.clock_end(status=Status.SUCCESS)
                return out
            except Exception as e:
                tracking_state.clock_end(status=Status.FAILURE)
                raise e
            finally:
                finally_block_time = datetime.datetime.utcnow()
                if tracking_state.status != Status.SUCCESS:
                    tracking_state.status = Status.FAILURE
                    # this assumes the task map only has things that have been processed, not
                    # nodes that have yet to be computed.
                    for task_name, task_run in tracking_state.task_map.items():
                        if task_run.status != Status.SUCCESS:
                            task_run.status = Status.FAILURE
                            task_run.end_time = finally_block_time
                            if task_run.error is None:  # we likely aborted it.
                                # Note if we start to do concurrent execution we'll likely
                                # need to adjust this.
                                task_run.error = ["Run was likely aborted."]
                        if task_run.end_time is None and task_run.status == Status.SUCCESS:
                            task_run.end_time = finally_block_time

                self.client.update_tasks(
                    dag_run_id=dag_run_id,
                    attributes=extract_attributes_from_tracking_state(tracking_state),
                    task_updates=extract_task_updates_from_tracking_state(tracking_state, fg),
                )
                self.client.log_dag_run_end(
                    dag_run_id=dag_run_id,
                    status=tracking_state.status.value,
                )
                logger.warning(
                    f"\nCaptured execution run. Results can be found at "
                    f"{self.dagworks_ui_url}/dashboard/project/{self.project_id}/runs/{dag_run_id}\n"
                )

    def validate(self, nodes_to_execute: List[node.Node]):
        pass
