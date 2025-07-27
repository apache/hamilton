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

import abc
import asyncio
import atexit
import datetime
import functools
import logging
import queue
import ssl
import threading
import time
from collections import defaultdict
from typing import Any, Callable, Dict, List, Union
from urllib.parse import urlencode

import aiohttp
import requests
from hamilton_sdk.api.projecttypes import GitInfo
from hamilton_sdk.tracking.utils import make_json_safe
from requests import HTTPError

logger = logging.getLogger(__name__)


class ResourceDoesNotExistException(Exception):
    def __init__(self, resource_type: str, resource_id: str, username: str):
        message = f"Resource {resource_type} with id {resource_id} does not exist/is accesible for user {username}."
        super().__init__(message)


class UnauthorizedException(Exception):
    def __init__(self, path: str, user: str):
        message = f"Unauthorized to access {path} by {user}."
        super().__init__(message)


def create_batch(batch: dict, dag_run_id: int):
    attributes = defaultdict(list)
    task_updates = defaultdict(list)
    for item in batch:
        if item["dag_run_id"] == dag_run_id:
            for attr in item["attributes"]:
                if attr is None:
                    continue
                attributes[attr["node_name"]].append(attr)
            for task_update in item["task_updates"]:
                if task_update is None:
                    continue
                task_updates[task_update["node_name"]].append(task_update)

    # We do not care about disambiguating here --  only one named attribute should be logged

    attributes_list = []
    for node_name in attributes:
        attributes_list.extend(attributes[node_name])
    # in this case we do care about order so we don't send double the updates.
    task_updates_list = [
        functools.reduce(lambda x, y: {**x, **y}, task_updates[node_name])
        for node_name in task_updates
    ]
    return attributes_list, task_updates_list


class HamiltonClient:
    @abc.abstractmethod
    def validate_auth(self):
        """Validates that authentication works against the DW API.
        Quick "phone-home" to ensure that everything is good to go.

        :raises UnauthorizedException: If the user is not authorized to access the Hamilton API.
        """
        pass

    @abc.abstractmethod
    def project_exists(self, project_id: int) -> bool:
        """Queries whether the project exists

        :param project_id: Project to ensure
        :return: True if the project exists, False if it was created.
        :raises UnauthorizedException: If the user is not authorized to access the Hamilton API.
        """
        pass

    @abc.abstractmethod
    def register_dag_template_if_not_exists(
        self,
        project_id: int,
        dag_hash: str,
        code_hash: str,
        nodes: List[dict],
        code_artifacts: List[dict],
        name: str,
        config: dict,
        tags: Dict[str, Any],
        code: List[dict],
        vcs_info: GitInfo,  # TODO -- separate this out so we can support more code version types -- just pass it directly to the client
    ) -> int:
        """Registers a project version with the Hamilton BE API.

        :param project_id: Project to register to
        :param dag_hash: Unique merkel hash of the DAG
        :param code_hash: Unique hash of the code used in the DAG/passed to the driver
        :param nodes: List of node objects
        :param code_artifacts:  List of code artifacts that we associate with this
        :param name: Name of the DAG
        :param config: Config used to create DAG
        :param tags: Tags to associate with the DAG
        :param code: List of tuples of (filename, file contents) for the code
        :param vcs_info: Version control information -- currently this is Git but we will likely add more
        @return: Version ID of the DAG template, for later use
        """
        pass

    @abc.abstractmethod
    def create_and_start_dag_run(
        self,
        dag_template_id: int,
        tags: Dict[str, str],
        inputs: Dict[str, Any],
        outputs: List[str],
    ) -> int:
        """Logs a DAG run to the Hamilton BE API.

        :param dag_template_id:
        :param dag_run: DAG run to log
        :param tags: Tags to log with the DAG run
        :param inputs: Inputs used to pass into the DAG
        :param outputs: Outputs used to query the DAG

        :return: Run ID
        """
        pass

    @abc.abstractmethod
    def update_tasks(
        self,
        dag_run_id: int,
        attributes: List[dict],
        task_updates: List[dict],
        in_samples: List[bool] = None,
    ):
        """Updates the tasks + attributes in a DAG run. Does not change the DAG run's status.

        :param dag_run_id: ID of the DAG run
        :param attributes: List of attributes
        :param task_updates:
        :param in_samples: List of bools indicating whether the task is in sample or not.
            Assumes 1-1 mapping with attributes & task_updates. This is a bit of a hack and only used for node updates.
        :return:
        """

    @abc.abstractmethod
    def log_dag_run_end(
        self,
        dag_run_id: int,
        status: str,
    ):
        """Logs the end of a DAG run.

        :param dag_run_id: ID of the DAG run.
        :param status: status of the DAG run.
        """
        pass


class BasicSynchronousHamiltonClient(HamiltonClient):
    def __init__(
        self,
        api_key: str,
        username: str,
        h_api_url: str,
        base_path: str = "/api/v1",
        verify: Union[str, bool] = True,
    ):
        """Initializes a Hamilton API client

         project: Project to save to
        :param api_key: API key to save to
        :param username: Username to authenticate against
        :param h_api_url: API URL for Hamilton API.
        :param base_path:
        :param verify: SSL verification to pass-through to requests
        """
        self.api_key = api_key
        self.username = username
        self.base_url = h_api_url + base_path
        self.verify = verify

        self.max_batch_size = 100
        self.flush_interval = 5
        # things that aren't serializeable
        self.data_queue = queue.Queue()
        self.running = True
        self.worker_thread = threading.Thread(target=self.worker)
        # When the main thread is joining, put `None` into queue to signal worker thread to end
        threading.Thread(
            target=lambda: threading.main_thread().join() or self.data_queue.put(None)
        ).start()
        self.worker_thread.start()

        # Makes sure the process stops even if in remote environment
        atexit.register(self.stop)

    def __getstate__(self):
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes. Always use the dict.copy()
        # method to avoid modifying the original state.
        state = self.__dict__.copy()
        # Remove the unpicklable entries.
        del state["data_queue"]
        del state["running"]
        del state["worker_thread"]
        return state

    def __setstate__(self, state):
        # Restore instance attributes (i.e., settings, etc).
        self.__dict__.update(state)
        self.data_queue = queue.Queue()
        self.running = True
        self.worker_thread = threading.Thread(target=self.worker)
        threading.Thread(
            target=lambda: threading.main_thread().join() or self.data_queue.put(None)
        ).start()
        self.worker_thread.start()
        atexit.register(self.stop)

    def worker(self):
        """Worker thread to process the queue."""
        batch = []
        last_flush_time = time.time()

        while self.running:
            try:
                # Wait up to flush_interval for new data
                item = self.data_queue.get(timeout=self.flush_interval)
                if item is None:
                    self.flush(batch)
                    return
                batch.append(item)

                # Check if batch is full or flush interval has passed
                if (
                    len(batch) >= self.max_batch_size
                    or (time.time() - last_flush_time) >= self.flush_interval
                ):
                    self.flush(batch)
                    batch = []
                    last_flush_time = time.time()
            except queue.Empty:
                # Flush on timeout if there's any data
                if batch:
                    self.flush(batch)
                    batch = []
                    last_flush_time = time.time()

    def flush(self, batch):
        """Flush the batch (send it to the backend or process it)."""
        logger.debug(f"Flushing batch: {len(batch)}")  # Replace with actual processing logic
        # group by dag_run_id -- just incase someone does something weird?
        dag_run_ids = set([item["dag_run_id"] for item in batch])
        for dag_run_id in dag_run_ids:
            attributes_list, task_updates_list = create_batch(batch, dag_run_id)
            response = requests.put(
                f"{self.base_url}/dag_runs_bulk?dag_run_id={dag_run_id}",
                json={
                    "attributes": make_json_safe(attributes_list),
                    "task_updates": make_json_safe(task_updates_list),
                },
                headers=self._common_headers(),
                verify=self.verify,
            )
            try:
                response.raise_for_status()
                logger.debug(f"Updated tasks for DAG run {dag_run_id}")
            except HTTPError:
                logger.exception(f"Failed to update tasks for DAG run {dag_run_id}")
                raise

    def stop(self):
        """Stop the logger and process remaining events."""
        # Signal the worker thread to stop processing new events
        self.running = False

        # Wait for the worker thread to process all remaining events
        self.worker_thread.join()

        # Process any events that might have been added to the queue
        # after the worker thread stopped
        while not self.data_queue.empty():
            try:
                item = self.data_queue.get_nowait()
                self.flush([item])
            except queue.Empty:
                break

    def _common_headers(self) -> Dict[str, Any]:
        """Yields the common headers for all requests.

        @return: a dictionary of headers.
        """
        return {"x-api-user": self.username, "x-api-key": self.api_key}

    def validate_auth(self):
        logger.debug(f"Validating auth against {self.base_url}/phone_home")
        response = requests.get(
            f"{self.base_url}/phone_home", headers=self._common_headers(), verify=self.verify
        )
        try:
            response.raise_for_status()
            logger.debug(f"Successfully validated auth against {self.base_url}/phone_home")
        except HTTPError as e:
            logger.error(f"Failed to validate auth against {self.base_url}/phone_home")
            if response.status_code // 100 == 4:
                raise UnauthorizedException("api/v1/auth/phone_home", self.username) from e
            raise

    def register_code_version_if_not_exists(
        self,
        project_id: int,
        code_hash: str,
        vcs_info: GitInfo,
        slurp_code: Callable[[], Dict[str, str]],
    ) -> int:
        logger.debug(f"Checking if code version {code_hash} exists for project {project_id}")
        response = requests.get(
            f"{self.base_url}/project_versions/exists?project_id={project_id}&code_hash={code_hash}",
            headers=self._common_headers(),
            verify=self.verify,
        )
        try:
            response.raise_for_status()
            logger.debug(f"Code version {code_hash} exists for project {project_id}")
            data = response.json()
            exists = data is not None
        except HTTPError as e:
            logger.debug(
                f"Failed to access project version {project_id} when looking for code hash: {code_hash}"
            )
            if response.status_code // 100 == 4:
                raise ResourceDoesNotExistException("code_version", code_hash, self.username) from e
            raise

        if exists:
            return data["id"]
        code_slurped = slurp_code()
        code_version_created = requests.post(
            f"{self.base_url}/project_versions?project_id={project_id}",
            headers=self._common_headers(),
            json={
                "code_hash": code_hash,
                "version_info": {
                    "git_hash": vcs_info.commit_hash,
                    "git_repo": vcs_info.repository,
                    "git_branch": vcs_info.branch,
                    "committed": vcs_info.committed,
                },  # TODO -- ensure serializable
                "version_info_type": "git",  # TODO -- wire this through appropriately
                "version_info_schema": 1,  # TODO -- wire this through appropriately
                "code_log": {"files": code_slurped},
            },
            verify=self.verify,
        )
        try:
            code_version_created.raise_for_status()
            logger.debug(f"Created code version {code_hash} for project {project_id}")
            return code_version_created.json()["id"]
        except HTTPError:
            logger.exception(
                f"Failed to create code version {code_hash} for project {project_id}. "
                f"Error was: {code_version_created.text}"
            )
            raise

    def project_exists(self, project_id: int) -> bool:
        logger.debug(f"Checking if project {project_id} exists")
        response = requests.get(
            f"{self.base_url}/projects/{project_id}",
            headers=self._common_headers(),
            verify=self.verify,
        )
        try:
            response.raise_for_status()
            logger.debug(f"Project {project_id} exists")
            return True
        except HTTPError as e:
            logger.debug(
                f"Project {project_id} does not exist/is accessible for user {self.username}"
            )
            if response.status_code // 100 == 4:
                raise ResourceDoesNotExistException(
                    "project", str(project_id), self.username
                ) from e
            raise

    def register_dag_template_if_not_exists(
        self,
        project_id: int,
        dag_hash: str,
        code_hash: str,
        nodes: List[dict],
        code_artifacts: List[dict],
        name: str,
        config: dict,
        tags: Dict[str, Any],
        code: List[dict],
        vcs_info: GitInfo,
    ) -> int:
        logger.debug(
            f"Checking if DAG template {dag_hash} exists for code hash: {code_hash}, dag hash: {dag_hash}, project {project_id}"
        )
        params = urlencode(
            {
                "project_id": project_id,
                "dag_hash": dag_hash,
                "code_hash": code_hash,
                "dag_name": name,
            }
        )
        response = requests.get(
            f"{self.base_url}/dag_templates/exists/?dag_hash={dag_hash}&{params}",
            headers=self._common_headers(),
            verify=self.verify,
        )
        response.raise_for_status()
        logger.debug(f"DAG template {dag_hash} exists for project {project_id}")
        data = response.json()
        exists = data is not None
        if exists:
            return data["id"]
        dag_template_created = requests.post(
            f"{self.base_url}/dag_templates?project_id={project_id}",
            json={
                "name": name,
                "template_type": "HAMILTON",
                "config": make_json_safe(config),
                "dag_hash": dag_hash,
                "tags": make_json_safe(tags),
                "nodes": nodes,
                "code_artifacts": code_artifacts,
                "code_log": {"files": code},
                "code_hash": code_hash,
                # Support more code version types
                "code_version_info_type": "git",
                "code_version_info": {
                    "git_hash": vcs_info.commit_hash,
                    "git_repo": vcs_info.repository,
                    "git_branch": vcs_info.branch,
                },
                "code_version_info_schema": 1,
            },
            headers=self._common_headers(),
            verify=self.verify,
        )
        try:
            dag_template_created.raise_for_status()
            logger.debug(f"Created DAG template {dag_hash} for project {project_id}")
            return dag_template_created.json()["id"]
        except HTTPError:
            logger.exception(
                f"Failed to create DAG template {dag_hash} for project {project_id}. Error: {dag_template_created.text}"
            )
            raise

    def create_and_start_dag_run(
        self, dag_template_id: int, tags: Dict[str, str], inputs: Dict[str, Any], outputs: List[str]
    ) -> int:
        logger.debug(f"Creating DAG run for project version {dag_template_id}")
        response = requests.post(
            f"{self.base_url}/dag_runs?dag_template_id={dag_template_id}",
            headers=self._common_headers(),
            json=make_json_safe(
                {
                    "run_start_time": datetime.datetime.utcnow(),  # TODO -- ensure serializable
                    "tags": tags,
                    # TODO: make the following replace with summary stats if it's large data, e.g. dataframes.
                    "inputs": make_json_safe(inputs),  # TODO -- ensure serializable
                    "outputs": outputs,
                    "run_status": "RUNNING",
                }
            ),
            verify=self.verify,
        )
        try:
            response.raise_for_status()
            logger.debug(f"Created DAG run for project version {dag_template_id}")
            return response.json()["id"]
        except HTTPError:
            logger.exception(
                f"Failed to create DAG run for project version {dag_template_id}. Error: {response.text}"
            )
            raise

    def update_tasks(
        self,
        dag_run_id: int,
        attributes: List[dict],
        task_updates: List[dict],
        in_samples: List[bool] = None,
    ):
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"Updating tasks for DAG run {dag_run_id} with {len(attributes)} "
                f"attributes and {len(task_updates)} task updates"
            )
        if in_samples is not None and not all(in_samples):
            assert len(in_samples) == len(attributes) == len(task_updates)
            for i, in_sample in enumerate(in_samples):
                # for each if the in_sample value is false, remove it from the list of attributes and task_updates
                if not in_sample:
                    attributes[i] = None
                    task_updates[i] = None
        self.data_queue.put(
            {"dag_run_id": dag_run_id, "attributes": attributes, "task_updates": task_updates}
        )

    def log_dag_run_end(self, dag_run_id: int, status: str):
        logger.debug(f"Logging end of DAG run {dag_run_id} with status {status}")
        response = requests.put(
            f"{self.base_url}/dag_runs/{dag_run_id}/",
            json=make_json_safe({"run_status": status, "run_end_time": datetime.datetime.utcnow()}),
            headers=self._common_headers(),
            verify=self.verify,
        )
        try:
            response.raise_for_status()
            logger.debug(f"Logged end of DAG run {dag_run_id}")
        except HTTPError:
            logger.exception(f"Failed to log end of DAG run {dag_run_id}. Error: {response.text}")
            raise


class BasicAsynchronousHamiltonClient(HamiltonClient):
    def __init__(
        self,
        api_key: str,
        username: str,
        h_api_url: str,
        base_path: str = "/api/v1",
        verify: Union[str, bool] = True,
    ):
        """Initializes an async Hamilton API client

         project: Project to save to
        :param api_key: API key to save to
        :param username: Username to authenticate against
        :param h_api_url: API URL for Hamilton API.
        :param base_path:
        :param verify: SSL verification options in requests format
        """
        self.api_key = api_key
        self.username = username
        self.base_url = h_api_url + base_path
        if verify is True:
            self.ssl = True
        elif verify is False:
            self.ssl = False
        else:
            self.ssl = ssl.create_default_context(cafile=verify)
        self.flush_interval = 5
        self.data_queue = asyncio.Queue()
        self.running = True
        self.max_batch_size = 100

    async def ainit(self):
        asyncio.create_task(self.worker())

    async def flush(self, batch):
        """Flush the batch (send it to the backend or process it)."""
        logger.debug(f"Flushing batch: {len(batch)}")  # Replace with actual processing logic
        # group by dag_run_id -- just incase someone does something weird?
        dag_run_ids = set([item["dag_run_id"] for item in batch])
        for dag_run_id in dag_run_ids:
            attributes_list, task_updates_list = create_batch(batch, dag_run_id)
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"{self.base_url}/dag_runs_bulk?dag_run_id={dag_run_id}",
                    json={
                        "attributes": make_json_safe(attributes_list),
                        "task_updates": make_json_safe(task_updates_list),
                    },
                    headers=self._common_headers(),
                    ssl=self.ssl,
                ) as response:
                    try:
                        response.raise_for_status()
                        logger.debug(f"Updated tasks for DAG run {dag_run_id}")
                    except HTTPError:
                        logger.exception(f"Failed to update tasks for DAG run {dag_run_id}")
                        # zraise

    async def worker(self):
        """Worker thread to process the queue"""
        batch = []
        last_flush_time = time.time()
        logger.debug("Starting worker")
        while True:
            logger.debug(
                f"Awaiting item from queue -- current batched # of items are: {len(batch)}"
            )
            try:
                item = await asyncio.wait_for(self.data_queue.get(), timeout=self.flush_interval)
                batch.append(item)
            except asyncio.TimeoutError:
                # This is fine, we just keep waiting
                pass
            else:
                if item is None:
                    await self.flush(batch)
                    return

            # Check if batch is full or flush interval has passed
            if (
                len(batch) >= self.max_batch_size
                or (time.time() - last_flush_time) >= self.flush_interval
            ):
                await self.flush(batch)
                batch = []
                last_flush_time = time.time()

    def _common_headers(self) -> Dict[str, Any]:
        """Yields the common headers for all requests.

        @return: a dictionary of headers.
        """
        return {"x-api-user": self.username, "x-api-key": self.api_key}

    async def validate_auth(self):
        logger.debug(f"Validating auth against {self.base_url}/phone_home")
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/phone_home",
                headers=self._common_headers(),
                ssl=self.ssl,
            ) as response:
                try:
                    response.raise_for_status()
                    logger.debug(f"Successfully validated auth against {self.base_url}/phone_home")
                except aiohttp.ClientResponseError as e:
                    logger.error(f"Failed to validate auth against {self.base_url}/phone_home")
                    if response.status // 100 == 4:
                        raise UnauthorizedException("api/v1/auth/phone_home", self.username) from e
                    raise

    async def register_code_version_if_not_exists(
        self,
        project_id: int,
        code_hash: str,
        vcs_info: GitInfo,
        slurp_code: Callable[[], Dict[str, str]],
    ) -> int:
        logger.debug(f"Checking if code version {code_hash} exists for project {project_id}")
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/project_versions/exists?project_id={project_id}&code_hash={code_hash}",
                headers=self._common_headers(),
                ssl=self.ssl,
            ) as response:
                try:
                    response.raise_for_status()
                    logger.debug(f"Code version {code_hash} exists for project {project_id}")
                    data = await response.json()
                    exists = data is not None
                except aiohttp.ClientResponseError as e:
                    logger.debug(
                        f"Failed to access project version {project_id} when looking for code hash: {code_hash}"
                    )
                    if response.status // 100 == 4:
                        raise ResourceDoesNotExistException(
                            "code_version", code_hash, self.username
                        ) from e
                    raise

        if exists:
            return data["id"]
        code_slurped = slurp_code()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"{self.base_url}/project_versions?project_id={project_id}",
                headers=self._common_headers(),
                json={
                    "code_hash": code_hash,
                    "version_info": {
                        "git_hash": vcs_info.commit_hash,
                        "git_repo": vcs_info.repository,
                        "git_branch": vcs_info.branch,
                        "committed": vcs_info.committed,
                    },  # TODO -- ensure serializable
                    "version_info_type": "git",  # TODO -- wire this through appropriately
                    "version_info_schema": 1,  # TODO -- wire this through appropriately
                    "code_log": {"files": code_slurped},
                },
                ssl=self.ssl,
            ) as response:
                try:
                    response.raise_for_status()
                    logger.debug(f"Created code version {code_hash} for project {project_id}")
                    return (await response.json())["id"]
                except aiohttp.ClientResponseError:
                    logger.exception(
                        f"Failed to create code version {code_hash} for project {project_id}. "
                        f"Error was: {await response.text()}"
                    )
                    raise

    async def project_exists(self, project_id: int) -> bool:
        logger.debug(f"Checking if project {project_id} exists")
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/projects/{project_id}",
                headers=self._common_headers(),
                ssl=self.ssl,
            ) as response:
                try:
                    response.raise_for_status()
                    logger.debug(f"Project {project_id} exists")
                    return True
                except aiohttp.ClientResponseError as e:
                    logger.debug(f"Project {project_id} does not exist")
                    if response.status // 100 == 4:
                        raise ResourceDoesNotExistException(
                            "project", str(project_id), self.username
                        ) from e
                    raise

    async def register_dag_template_if_not_exists(
        self,
        project_id: int,
        dag_hash: str,
        code_hash: str,
        nodes: List[dict],
        code_artifacts: List[dict],
        name: str,
        config: dict,
        tags: Dict[str, Any],
        code: List[dict],
        vcs_info: GitInfo,
    ) -> int:
        logger.debug(
            f"Checking if DAG template {dag_hash} exists for code hash: {code_hash}, dag hash: {dag_hash}, project {project_id}"
        )
        params = urlencode(
            {
                "project_id": project_id,
                "dag_hash": dag_hash,
                "code_hash": code_hash,
                "dag_name": name,
            }
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/dag_templates/exists/?dag_hash={dag_hash}&{params}",
                headers=self._common_headers(),
                ssl=self.ssl,
            ) as response:
                try:
                    response.raise_for_status()
                    logger.debug(f"DAG template {dag_hash} exists for project {project_id}")
                    data = await response.json()
                except aiohttp.ClientResponseError:
                    logger.exception(f"Failed to get DAG template tasks for project {project_id}")
                    raise
        exists = data is not None
        if exists:
            return data["id"]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/dag_templates?project_id={project_id}",
                json={
                    "name": name,
                    "template_type": "HAMILTON",
                    "config": make_json_safe(config),
                    "dag_hash": dag_hash,
                    "tags": make_json_safe(tags),
                    "nodes": nodes,
                    "code_artifacts": code_artifacts,
                    "code_log": {"files": code},
                    "code_hash": code_hash,
                    # Support more code version types
                    "code_version_info_type": "git",
                    "code_version_info": {
                        "git_hash": vcs_info.commit_hash,
                        "git_repo": vcs_info.repository,
                        "git_branch": vcs_info.branch,
                    },
                    "code_version_info_schema": 1,
                },
                headers=self._common_headers(),
                ssl=self.ssl,
            ) as response:
                try:
                    response.raise_for_status()
                    logger.debug(f"Created DAG template {dag_hash} for project {project_id}")
                    return (await response.json())["id"]
                except aiohttp.ClientResponseError:
                    logger.exception(
                        f"Failed to create DAG template {dag_hash} for project {project_id}. Error: {await response.text()}"
                    )
                    raise

    async def create_and_start_dag_run(
        self, dag_template_id: int, tags: Dict[str, str], inputs: Dict[str, Any], outputs: List[str]
    ) -> int:
        logger.debug(f"Creating DAG run for project version {dag_template_id}")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/dag_runs?dag_template_id={dag_template_id}",
                json=make_json_safe(
                    {
                        "run_start_time": datetime.datetime.utcnow(),  # TODO -- ensure serializable
                        "tags": tags,
                        # TODO: make the following replace with summary stats if it's large data, e.g. dataframes.
                        "inputs": make_json_safe(inputs),  # TODO -- ensure serializable
                        "outputs": outputs,
                        "run_status": "RUNNING",
                    }
                ),
                headers=self._common_headers(),
                ssl=self.ssl,
            ) as response:
                try:
                    response.raise_for_status()
                    logger.debug(f"Created DAG run for project version {dag_template_id}")
                    return (await response.json())["id"]
                except aiohttp.ClientResponseError:
                    logger.exception(
                        f"Failed to create DAG run for project version {dag_template_id}. Error: {response.text}"
                    )
                    raise

    async def update_tasks(
        self,
        dag_run_id: int,
        attributes: List[dict],
        task_updates: List[dict],
        in_samples: List[bool] = None,
    ):
        logger.debug(
            f"Updating tasks for DAG run {dag_run_id} with {len(attributes)} "
            f"attributes and {len(task_updates)} task updates"
        )
        await self.data_queue.put(
            {"dag_run_id": dag_run_id, "attributes": attributes, "task_updates": task_updates}
        )

    async def log_dag_run_end(self, dag_run_id: int, status: str):
        logger.debug(f"Logging end of DAG run {dag_run_id} with status {status}")
        url = f"{self.base_url}/dag_runs/{dag_run_id}/"
        data = make_json_safe({"run_status": status, "run_end_time": datetime.datetime.utcnow()})
        headers = self._common_headers()
        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=data, headers=headers, ssl=self.ssl) as response:
                try:
                    response.raise_for_status()
                    logger.debug(f"Logged end of DAG run {dag_run_id}")
                except aiohttp.ClientResponseError:
                    logger.exception(
                        f"Failed to log end of DAG run {dag_run_id}. Error: {response.text}"
                    )
                    raise
