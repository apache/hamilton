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

import collections
import logging
from typing import List, Optional

from common import django_utils
from ninja import Router
from ninja.errors import HttpError
from ninja.params import Query
from trackingserver_base.permissions.base import permission
from trackingserver_base.permissions.permissions import (
    user_can_get_dag_runs,
    user_can_get_latest_dag_runs,
    user_can_get_project_by_id,
    user_can_write_to_dag_run,
    user_can_write_to_dag_template,
)
from trackingserver_run_tracking.models import DAGRun, NodeRun, NodeRunAttribute
from trackingserver_run_tracking.schema import (
    CatalogZoomResponse,
    DAGRunIn,
    DAGRunOut,
    DAGRunOutWithData,
    DagRunsBulkRequest,
    DAGRunUpdate,
    NodeRunAttributeOut,
    NodeRunIn,
    NodeRunOutWithAttributes,
    NodeRunOutWithExtraData,
)
from trackingserver_template.models import NodeTemplate
from trackingserver_template.schema import CodeArtifactOut, NodeTemplateOut

logger = logging.getLogger(__name__)

router = Router(tags=["run_tracking"])


@router.post("/v1/dag_runs", response=DAGRunOut, tags=["run_tracking"])
@permission(user_can_write_to_dag_template)
async def create_dag_run(request, dag_template_id: int, dag_run: DAGRunIn) -> DAGRunOut:
    """Creates a DAG run, no data in it yet.

    @param dag_template_id:
    @param dag_run:
    @return:
    """
    user, teams = request.auth
    logger.info(f"Creating DAG run for dag template: {dag_template_id} for user: {user.email}")
    dag_run_created = await DAGRun.objects.acreate(
        **dag_run.dict(), dag_template_id=dag_template_id, launched_by_id=user.id
    )
    logger.info(f"Created DAG run for dag template: {dag_template_id}")
    return DAGRunOut.from_orm(dag_run_created)


@router.get("/v1/dag_runs/latest/", response=List[DAGRunOut], tags=["run_tracking"])
@permission(user_can_get_latest_dag_runs)
async def get_latest_dag_runs(
    request,
    project_id: int = None,
    dag_template_id: int = None,
    limit: int = 100,
    offset: int = 0,
) -> List[DAGRunOut]:
    """Gets a list of DAG runs. This accepts one (and only one of) the following:
        - project_id
        - dag_template_id

    @param project_id:
    @param dag_template_id:
    @param limit:
    @param offset:
    @return list of DAG runs:
    """
    user, teams = request.auth
    logger.info(
        f"Getting DAG runs for user: {user.email}, "
        f"project: {project_id}"
        f"dag template: {dag_template_id}"
    )
    key_kwargs = {
        "dag_template__project_id": project_id,
        "dag_template_id": dag_template_id,
    }
    key_kwargs = {k: v for k, v in key_kwargs.items() if v is not None}
    if len(key_kwargs) > 1:
        raise HttpError(
            422,
            f"Can only specify one of project_id/dag_template_id, "
            f"got: project_id={project_id}, dag_template_id={dag_template_id}",
        )
    dag_runs = await django_utils.amap(
        DAGRunOut.create_with_username,
        DAGRun.objects.filter(**key_kwargs, **{"dag_template__is_active": True})
        .order_by("-created_at")[offset : limit + offset]
        .prefetch_related("launched_by")
        .all(),
    )
    logger.info(f"Got {len(dag_runs)} DAG runs for user: {user.email}")
    return dag_runs


@router.get("/v1/dag_runs/{dag_run_ids}", response=List[DAGRunOutWithData], tags=["run_tracking"])
@permission(user_can_get_dag_runs)
async def get_dag_runs(
    request,
    dag_run_ids: str,
    attrs: List[str] = Query(default=None, alias="attr"),  # noqa
) -> List[DAGRunOutWithData]:
    """Queries a DAG run with all the data.
    Note that you must pass an attribute filter, indicating
    the attributes about which you care.

    @param attrs:
    @param dag_run_id:
    @return:
    """
    user, teams = request.auth
    if attrs is None:
        attrs = []
    logger.info(f"Getting DAG run(s): {dag_run_ids} for user: {user.email}")
    dag_run_ids_parsed = [int(dag_run_id) for dag_run_id in dag_run_ids.split(",")]
    all_dag_run_runs = [
        item async for item in DAGRun.objects.filter(id__in=dag_run_ids_parsed).all()
    ]
    all_nodes = await django_utils.alist(
        NodeRun.objects.filter(dag_run_id__in=dag_run_ids_parsed).all()
    )
    all_attributes = await django_utils.amap(
        NodeRunAttributeOut.from_orm,
        NodeRunAttribute.objects.filter(dag_run_id__in=dag_run_ids_parsed, type__in=attrs).all(),
    )
    all_results = []
    for dag_run_id in dag_run_ids_parsed:
        attributes = [attribute for attribute in all_attributes if attribute.dag_run == dag_run_id]
        nodes = [node for node in all_nodes if node.dag_run_id == dag_run_id]
        dag_run_candidates = [dag_run for dag_run in all_dag_run_runs if dag_run.id == dag_run_id]
        if len(dag_run_candidates) == 0:
            logger.warning(f"DAG run with ID {dag_run_id} does not exist.")
            raise HttpError(404, f"DAG run with ID {dag_run_id} does not exist.")
        (dag_run,) = dag_run_candidates
        attributes_grouped_by_node = collections.defaultdict(list)
        for attribute in attributes:
            attributes_grouped_by_node[attribute.node_name].append(attribute)
        out = DAGRunOutWithData.from_data(dag_run, [])
        for node in nodes:
            out.node_runs.append(
                NodeRunOutWithAttributes.from_data(
                    node,
                    attributes=attributes_grouped_by_node[node.node_name],
                )
            )
        all_results.append(out)
        logger.info(f"Got DAG run: {dag_run_id}")
    return all_results


@router.put("/v1/dag_runs/{dag_run_id}/", response=DAGRunOut, tags=["run_tracking"])
@permission(user_can_write_to_dag_run)
async def update_dag_run(request, dag_run_id: int, dag_run: DAGRunUpdate) -> DAGRunOut:
    """Creates a DAG run, no data in it yet.

    @param dag_template_id:
    @param dag_run:
    @return:
    """
    user, teams = request.auth
    logger.info(f"Updating DAG run for dag template: {dag_run_id} for user: {user.email}")
    try:
        dag_run_in_db = await DAGRun.objects.aget(id=dag_run_id)
    except DAGRun.DoesNotExist:
        raise HttpError(404, f"DAG run with ID {dag_run_id} does not exist.") from None
    for attr, value in dag_run.dict(exclude_unset=True).items():
        if attr == "upsert_tags":
            upsert_tags = {} if dag_run.upsert_tags is None else dag_run.upsert_tags
            dag_run_in_db.tags = {**dag_run_in_db.tags, **upsert_tags}
        setattr(dag_run_in_db, attr, value)
    await dag_run_in_db.asave()
    logger.info(f"Updated DAG run for dag template: {dag_run_id}")
    # TODO -- unify this with the above, we're doing way too many db queries...
    # We should just be doing one, but as django doesn't appear to support postgres's
    # on_conflict for json fields and we want to upsert, we'll probably have to do 2
    saved = await DAGRun.objects.aget(id=dag_run_id)
    return DAGRunOut.from_orm(saved)


def process_task_updates(node_runs: List[NodeRunIn], dag_run_id: int) -> List[NodeRun]:
    """Processes task updates, returning a list of NodeRuns to save.
    TODO -- squash any task updates on the same task, resolving conflicts
    (E.G. if one is SUCCESS and one is FAILURE).

    @param node_run_in:
    @return:
    """
    node_updates = {}  # Map of node_name to NodeRun
    # We update this as we go along
    for node_run in node_runs:
        data = node_run.dict(exclude_unset=True)
        data["dag_run_id"] = dag_run_id
        name = node_run.node_name
        if name in node_updates:
            # TODO -- resolve conflicts in a sane way
            # See TODO in README
            for key, value in data.items():
                setattr(node_updates[name], key, value)
        else:
            node_updates[name] = NodeRun(**data)
    return list(node_updates.values())


@router.put("/v1/dag_runs_bulk", response=None, tags=["run_tracking"])
@permission(user_can_write_to_dag_run)
async def bulk_log(
    request,
    bulk_log_data: DagRunsBulkRequest,
    dag_run_id: int,
):
    """Performs a bulk logging operation for a DAG run.
    Note that these do not need to know the IDs of anything besides the DAG Run,
    and we will likely have it use a UUID for the DAG run ID (the one the client creates).

    This will do one of the following:

    1. Assert that the DAGRun exists
    2. Gather all the associated NodeTemplates by referencing the node names
    3. Perform an in-memory join with relevant node_runs to create all the NodeRun objects
    4. Bulk create all the NodeRun objects
    5. Bulk create all the NodeRunAttribute objects

    Note that this might not work if an attrbute is logged *before* a node.

    In that case, we'll likely do the following:
    1. Change foreign key from noderun to be a string with an index on it
    2. This will allow us to bulk create all the NodeRunAttributes
    3. We would still join node run to template

    Note that we would have to add DAGRun as a foreign key here.


    Then the query patterns we want:
    1. Query all nodes/attributes for a given DAG run
    2. Query all attributes for a node
    3. Query all iterations of a previous attribute for that node

    Should be easy to do.

    Will likely do the second one -- it simplifies it and doesn't require
    us to do a lot of ugly joins to know what to do.

    @param dag_run_id:
    @param dag_run:
    @param attributes:
    @param task_updates:
    @return:
    """
    node_run_attributes = bulk_log_data.attributes
    node_run_updates = bulk_log_data.task_updates
    try:
        dag_run = await DAGRun.objects.aget(id=dag_run_id)
    except DAGRun.DoesNotExist:
        raise HttpError(404, f"DAG run with ID {dag_run_id} does not exist.") from None

    task_updates_to_save = process_task_updates(node_run_updates, dag_run_id=dag_run.id)
    # TODO -- determine if we can do this in one pass
    # E.G. if it allows us to set, say, end_time,
    # Then we can set *just* run_status, and if end_time wasn't included in the constructor
    # This is optimistic -- we hope that we can do this in one pass, allowing us to just process a list of updates
    # If not, we have two strategies:
    #     > Query then merge
    #     > Break up by field (this is simple -- we have end_time/run_status which are the only ones that should be updated...
    # Note that, given that we have run_status = RUNNING -> SUCCESS, FAILED, we konw the status transitions are safe,
    # So maybe it just works to update everything in one pass?
    # Also maybe we can use this? https://github.com/SectorLabs/django-postgres-extra
    logger.info(f"Updating {len(task_updates_to_save)} task updates for dag run: {dag_run_id}")
    await NodeRun.objects.abulk_create(
        task_updates_to_save,
        update_conflicts=True,
        update_fields=[
            "end_time",
            "status",
        ],
        unique_fields=["dag_run_id", "node_name"],
    )
    logger.info(f"Updated {len(task_updates_to_save)} task updates for dag run: {dag_run_id}")
    node_attributes_to_create = [
        NodeRunAttribute(**attribute.dict(), dag_run_id=dag_run.id)
        for attribute in node_run_attributes
    ]
    logger.info(
        f"Creating {len(node_attributes_to_create)} node attributes for dag run: {dag_run_id}"
    )
    await NodeRunAttribute.objects.abulk_create(node_attributes_to_create)
    logger.info(
        f"Created {len(node_attributes_to_create)} node attributes for dag run: {dag_run_id}"
    )


@router.get(
    "/v1/node_runs/by_run_ids/{dag_run_ids}",
    response=List[Optional[NodeRunOutWithAttributes]],
    tags=["run_tracking", "cross-runs", "FE-only", "node_tracking"],
)
@permission(user_can_get_dag_runs)
async def get_node_run_for_dags(
    request,
    dag_run_ids: str,
    node_name: str,
) -> List[Optional[NodeRunOutWithAttributes]]:
    """Gives a specific set of node runs for a certain set of attribute types.
    This enables the DAG viz in the UI to compare nodes with attributes across runs.
    Gives back all node attributes.

    @param request: Django request
    @param dag_run_ids: Comma-separated list of DAG run IDs
    @param node_name: name of the node
    @return: List of node runs
    """
    user, teams = request.auth
    logger.info(
        f"Getting node runs for node: {node_name} for dag runs: {dag_run_ids} for all attributes for user: {user.email}"
    )
    dag_run_ids_parsed = [int(dag_run_id) for dag_run_id in dag_run_ids.split(",")]
    all_attributes = await django_utils.amap(
        NodeRunAttributeOut.from_orm,
        NodeRunAttribute.objects.filter(
            dag_run_id__in=dag_run_ids_parsed, node_name=node_name
        ).all(),
    )
    all_nodes = await django_utils.alist(
        NodeRun.objects.filter(dag_run_id__in=dag_run_ids_parsed, node_name=node_name).all()
    )

    out = []
    for dag_run_id in dag_run_ids_parsed:
        applicable_nodes = [node for node in all_nodes if node.dag_run_id == dag_run_id]
        if len(applicable_nodes) == 0:
            out.append(None)
            continue
        (node,) = applicable_nodes
        out.append(
            NodeRunOutWithAttributes.from_data(
                node,
                [attribute for attribute in all_attributes if attribute.dag_run == dag_run_id],
            ),
        )
    num_attributes = sum([len(item.attributes) if item else 0 for item in out])
    logger.info(
        f"Got {len([item for item in out if item])} nodes and {num_attributes} attributes for node: {node_name} "
        f"for dag runs: {dag_run_ids} for user: {user.email}"
    )
    return out


@router.get(
    "/v1/node_runs/{node_template_name}",
    response=CatalogZoomResponse,
    tags=["run_tracking", "cross-runs", "FE-only"],
)
@permission(user_can_get_project_by_id)
async def get_latest_template_runs(
    request,
    node_template_name: str,
    project_id: int,
    limit: int = 100,
    offset: int = 0,
) -> CatalogZoomResponse:
    """Gets the latest runs for a given node template name.
    Specifically for expanding on the catalog view.

    @param node_template_name:
    @param project_id:
    @param limit:
    @param offset:
    @return:
    """
    user, teams = request.auth
    logger.info(
        f"Getting latest runs for node template: {node_template_name} for user: {user.email} for project: {project_id}"
    )
    node_runs = await django_utils.alist(
        NodeRun.objects.filter(
            node_template_name=node_template_name,
            dag_run__dag_template__project_id=project_id,
            dag_run__dag_template__is_active=True,
        )
        .prefetch_related("dag_run__dag_template", "dag_run")
        .order_by("-created_at")[offset : limit + offset]
        .all()
    )
    all_dag_versions = [item.dag_run.dag_template_id for item in node_runs]
    # Breaking it into two cause our data model isn't perfect yet
    # consider making the foreign key to node template?
    node_templates = await django_utils.alist(
        NodeTemplate.objects.filter(dag_template_id__in=all_dag_versions, name=node_template_name)
        .prefetch_related("code_artifacts")
        .all()
    )
    logger.info(
        f"Got latest runs for node template: {node_template_name} for user: {user.email} for project: {project_id}"
        f"got {len(node_runs)} node runs and {len(node_templates)} node templates."
    )
    code_artifacts = list(
        {
            code_artifact
            for node_template in node_templates
            for code_artifact in node_template.code_artifacts.all()
        }
    )
    return CatalogZoomResponse(
        node_runs=[
            NodeRunOutWithExtraData.from_orm(node_run, dag_template_id=dag_template_id)
            for (node_run, dag_template_id) in zip(node_runs, all_dag_versions)
        ],
        node_templates=[
            NodeTemplateOut.from_orm(node_template) for node_template in node_templates
        ],
        code_artifacts=[
            CodeArtifactOut.from_orm(code_artifact)
            for code_artifact in code_artifacts
            if code_artifact is not None
        ],
    )
    # return node_runs


# @router.get(
#     "/v1/node_run_attributes",
#     response=DAGRunOut,
#     tags=["run_tracking"]
# )
# async def historical_node_attributes(
#         node_name: str,
#         attribute_names: List[str],
#         limit: int = 1000,
#         offset: int = 0
# ) -> List[NodeRunAttributeOut]:
#     """Queries prior attributes for a specific node.
#     This is an historical query that can query all previous
#     ones to give, say, a profile/histogram.
#
#     @param node_name:
#     @param attribute_name:
#     @param limit:
#     @param offset:
#     @return:
#     """
#
#     logger.info(f"Getting {len(attribute_names)} attributes for node: {node_name}")
#     attributes = await django_utils.amap(
#         NodeRunAttributeOut.from_orm,
#         NodeRunAttribute.objects.filter(
#             node_name=node_name,
#             name_in=attribute_names).order_by("-created_at")[offset:limit + offset].all()
#     )
#     logger.info(f"Got {len(attribute_names)} attributes for node: {node_name}")
#     return attributes
