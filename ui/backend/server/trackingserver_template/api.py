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

import asyncio
import logging
import time
from typing import List, Optional

from common.django_utils import alist
from django.db.models import F, Window
from django.db.models.functions import RowNumber
from ninja import Router
from ninja.errors import HttpError
from trackingserver_base import blob_storage
from trackingserver_base.permissions.base import permission
from trackingserver_base.permissions.permissions import (
    user_can_get_dag_template,
    user_can_get_dag_templates,
    user_can_get_project_by_id,
    user_can_update_dag_template,
    user_can_write_to_project,
)
from trackingserver_template.models import (
    CodeArtifact,
    DAGTemplate,
    NodeTemplate,
    NodeTemplateCodeArtifactRelation,
)
from trackingserver_template.schema import (
    CatalogResponse,
    CodeArtifactOut,
    DAGTemplateIn,
    DAGTemplateOut,
    DAGTemplateOutWithData,
    DAGTemplateUpdate,
    NodeTemplateOut,
)

logger = logging.getLogger(__name__)
router = Router(tags=["projects"])

blob_store = blob_storage.get_blob_store()


@router.post("/v1/dag_templates", response=DAGTemplateOut, tags=["projects", "templates"])
@permission(user_can_write_to_project)
async def create_dag_template(
    request, project_id: int, dag_template: DAGTemplateIn
) -> DAGTemplateOut:
    """Creates a project version for a given project.

    @param request:
    @param project_version_id:
    @param dag_template:
    @return:
    """
    user, orgs = request.auth
    logger.info(f"Creating DAG template for project version: {project_id} for {user.email}")

    code_log = dag_template.code_log
    if code_log is not None:
        logger.info(f"Saving code log for project {project_id} for {user.email}")
        code_log_url = await blob_store.write_obj("project" + str(project_id), code_log.dict())
        logger.info(f"Stored code for project {project_id} for {user.email} at {code_log_url}")
        code_log_store = blob_store.store()
        code_log_schema_version = 1
    else:
        code_log_url = None
        code_log_store = "none"
        code_log_schema_version = None

    dag_template_created = await DAGTemplate.objects.acreate(
        project_id=project_id,
        name=dag_template.name,
        template_type=dag_template.template_type,
        config=dag_template.config,
        dag_hash=dag_template.dag_hash,
        is_active=True,
        tags=dag_template.tags,
        code_hash=dag_template.code_hash,
        code_version_info_type=dag_template.code_version_info_type,
        code_version_info=dag_template.code_version_info,
        code_version_info_schema=dag_template.code_version_info_schema,
        code_log_store=code_log_store,
        code_log_url=code_log_url,
        code_log_schema_version=code_log_schema_version,
    )
    logger.info(f"Created DAG template for project : {project_id} for {user.email}")
    code_artifacts_created = await CodeArtifact.objects.abulk_create(
        [
            CodeArtifact(**code_artifact.dict(), dag_template_id=dag_template_created.id)
            for code_artifact in dag_template.code_artifacts
        ],
        ignore_conflicts=False,
    )

    code_artifacts_by_name = {item.name: item for item in code_artifacts_created}

    node_templates_to_create = []
    through_models = []

    for node in dag_template.nodes:
        node_template = NodeTemplate(
            **{key: value for key, value in node.dict().items() if key != "code_artifact_pointers"},
            dag_template_id=dag_template_created.id,
        )
        node_templates_to_create.append(node_template)
    created_nodes = await NodeTemplate.objects.abulk_create(node_templates_to_create)
    logger.info(
        f"Created {len(created_nodes)} nodes for project version {project_id} for {user.email}"
    )

    nodes_created_by_name = {item.name: item for item in created_nodes}
    for node in dag_template.nodes:
        for i, code_pointer in enumerate(node.code_artifact_pointers):
            # TODO -- figure out what to do if this isn't there -- this should be an error, no?
            # If so, we should validate earlier...
            # For now we're going to log a warning
            code_artifact = code_artifacts_by_name.get(code_pointer)
            if code_artifact is None:
                logger.warning(
                    f"Code artifact with name: {code_pointer} not found for node: {node.name}"
                )
                continue
            through_models.append(
                NodeTemplateCodeArtifactRelation(
                    node_template_id=nodes_created_by_name[node.name].id,
                    code_artifact_id=code_artifact.id,
                    is_primary=i == 0,  # First one will be primary
                )
            )
    await NodeTemplateCodeArtifactRelation.objects.abulk_create(through_models)
    logger.info(
        f"Created {len(created_nodes)} nodes & {len(code_artifacts_created)} artifacts "
        f"for project version {project_id} for {user.email}. Created {len(through_models)} relations."
    )
    return DAGTemplateOut.from_orm(dag_template_created)


@router.get(
    "/v1/dag_templates/exists/", response=Optional[DAGTemplateOut], tags=["projects", "templates"]
)
@permission(user_can_get_project_by_id)
async def dag_template_exists(
    request,
    dag_hash: str,
    code_hash: str,
    dag_name: str,
    project_id: int,
):
    """Checks if a DAG template exists for a given project version and DAG hash.

    @param request: The request
    @param dag_hash: The DAG hash to check for
    @param project_id: The project version to check for

    @return: True if the DAG template exists, False otherwise.
    """
    try:
        logger.info(
            f"Checking if DAG template exists for project version: {project_id} with hash: {dag_hash}"
        )
        dag_template = await DAGTemplate.objects.aget(
            project_id=project_id, dag_hash=dag_hash, name=dag_name, code_hash=code_hash
        )
        return DAGTemplateOut.from_orm(dag_template)
    except DAGTemplate.DoesNotExist:
        logger.info(f"DAG template does not exist for project: {project_id} with hash: {dag_hash}")
        return None


@router.get(
    "/v1/dag_templates/latest/", response=List[DAGTemplateOut], tags=["projects", "templates"]
)
@permission(user_can_get_dag_templates)
async def get_latest_dag_templates(
    request,
    project_id: int,
    limit: int = 100,
    offset: int = 0,
) -> List[DAGTemplateOut]:
    """Gets all DAG templates for a given project version.
    Note that this does not return the nodes, just the templates, as this is a bulk query.

    @param request: The request
    @param project_id: The project to get DAG templates for
    @param limit: The maximum number of DAG templates to return
    @param offset: The offset to start at
    @return: A list of DAG templates
    """
    user, orgs = request.auth
    logger.info(f"Getting all DAG templates for project version: {project_id} for {user.email}")
    out = [
        item
        async for item in DAGTemplate.objects.filter(
            project_id=project_id, is_active=True
        ).order_by("-created_at")[offset : offset + limit]
    ]
    logger.info(
        f"Got all DAG templates for project version: {project_id} for {user.email}, retrieved {len(out)}"
    )
    return [DAGTemplateOut.from_orm(dag_template) for dag_template in out]


@router.get(
    "/v1/dag_templates/catalog/",
    response=CatalogResponse,
    tags=["projects", "templates", "FE-only"],
)
@permission(user_can_get_dag_templates)
async def get_dag_template_catalog(
    request,
    project_id: int = None,
    offset: int = 0,
    limit: int = 1000,
) -> CatalogResponse:
    """Gets a massive list of the previous node templates -- note that this is a WIP, we may look for it to be distinct, but for
    now we just want to get the last few.

    Then, when someone opens it up, we'll do a full query for the corresponding node runs to display in the catalog.

    This should probably be replaced by a materialized view, which can aggregate distinct across every one, grouping and
    getting the first. That said, that's a little complicated.

    @param offset:
    @param limit:
    @param project_id: ID of the associated project
    @return: A list of node templates that have been associated with DAG templates with that project.
    """
    # TODO -- see how slow this is...
    user, orgs = request.auth
    t1 = time.time()
    logger.info(
        f"Getting last {limit} DAG template catalog for project ID: {project_id} for user: {user.email}"
    )
    # Aggregations
    # These will likely do fine, but the best way to do this is to create a materialized view with a catalog table
    # This will be running in the background and do this for each project, ideally continually updating
    # For now we can aggregate, and let's see how this scales
    # We have two options -- leaning towards the second option...

    # Option 1:
    # We don't have an index on created_at, so I'm just using -id
    # Note that this is... suboptimal -- we shouldn't just rely on monotonic IDs, but it'll do what I want for now
    # qs = (
    #         NodeTemplate
    #         .objects
    #         .filter(**filter_kwargs)
    #         .order_by(
    #             "name",
    #             "-created_at"
    #         ).distinct("name")[offset:limit + offset]
    # )
    # all_node_templates = [item async for item in qs]
    # print(await qs.aexplain())

    # Option 2:
    # Find the latest id for each name
    # query = (
    #         NodeTemplate
    #         .objects
    #         .filter(**filter_kwargs)
    #         .values("name")
    #         .annotate(max_id=Max('id'))
    #         .values_list('max_id', flat=True)[offset: limit+offset])
    # latest_ids = [
    #     item async for item in query
    # ]
    # all_node_templates = [
    #     item async for item in NodeTemplate.objects.filter(id__in=latest_ids)
    # ]

    # Note we can optionally do this with the Subquery() function, although I'm not sure if it's faster
    # We will use this for now

    # Option 3: utilize window functions
    # Define the window function
    window = Window(expression=RowNumber(), partition_by=F("name"), order_by=F("id").desc())

    # Annotate each NodeTemplate with its row number within its name partition
    queryset = (
        NodeTemplate.objects.filter(
            dag_template__project_id=project_id, dag_template__is_active=True
        )
        .annotate(row_num=window)
        .filter(row_num=1)
        .prefetch_related("code_artifacts")[offset : limit + offset]
    )

    all_node_templates = [item async for item in queryset]

    # Fetch the result

    # print(await queryset.aexplain())

    t2 = time.time()
    logger.info(
        f"Retrieved last {limit} project ID: {project_id} for user: {user.email} in {time.time() - t1} seconds. Got {len(all_node_templates)} nodes."
    )
    # TODO -- see how slow this is
    node_templates = [
        NodeTemplateOut.from_orm(node_template) for node_template in all_node_templates
    ]
    for i, node_template in enumerate(node_templates):
        node_template.dag_template = all_node_templates[i].dag_template_id
    code_artifacts = list(
        {
            code_artifact
            for node_template in all_node_templates
            for code_artifact in node_template.code_artifacts.all()
        }
    )
    out = CatalogResponse(
        nodes=node_templates[:],
        code_artifacts=code_artifacts,
    )
    logger.info(
        f"Parsed last {limit} project ID: {project_id} for user: {user.email} in {time.time() - t2} "
        f"seconds. Got {len(out.nodes)} nodes and {len(out.code_artifacts)} code artifacts."
    )
    return out


@router.get(
    "/v1/dag_templates/{str:dag_template_ids}",
    response=List[DAGTemplateOutWithData],
    tags=["templates"],
)
@permission(user_can_get_dag_template)
async def get_full_dag_templates(request, dag_template_ids: str) -> List[DAGTemplateOutWithData]:
    """Gets the full DAG template, joined with the created nodes, for the given DAG template ID.
    @param request: The request
    @return:  The full DAG template (with nodes).
    """
    dag_template_ids_parsed = [int(item) for item in dag_template_ids.split(",")]
    out = []
    all_nodes = [
        item
        async for item in NodeTemplate.objects.filter(dag_template_id__in=dag_template_ids_parsed)
        .prefetch_related("code_artifacts")
        .all()
    ]
    all_code_artifacts = [
        item
        async for item in CodeArtifact.objects.filter(dag_template_id__in=dag_template_ids_parsed)
    ]

    all_dag_templates_retrieved = await alist(
        DAGTemplate.objects.filter(id__in=dag_template_ids_parsed, is_active=True)
    )

    for dag_template_id in dag_template_ids_parsed:
        relevant_dag_templates = [
            item for item in all_dag_templates_retrieved if item.id == dag_template_id
        ]
        if len(relevant_dag_templates) == 0:
            logger.exception(f"No DAG template with ID: {dag_template_id}")
            raise HttpError(status_code=404, message=f"No DAG template with ID: {dag_template_id}")
        (dag_template_retrieved,) = relevant_dag_templates
        user, orgs = request.auth
        logger.info(f"Getting full DAG template for {user.email} with ID: {dag_template_id}")
        nodes_in_template = [item for item in all_nodes if item.dag_template_id == dag_template_id]
        code_artifacts_in_template = [
            item for item in all_code_artifacts if item.dag_template_id == dag_template_id
        ]
        # TODO -- use a bulk query
        nodes_out = [NodeTemplateOut.from_orm(node) for node in nodes_in_template]
        code_artifacts_out = [
            CodeArtifactOut.from_orm(code_artifact) for code_artifact in code_artifacts_in_template
        ]
        dag_template = DAGTemplateOut.from_orm(dag_template_retrieved)
        logger.info(
            f"Retrieved full DAG template for {user.email} "
            f"with ID: {dag_template_id} with {len(nodes_out)} "
            f"nodes and {len(code_artifacts_in_template)} code artifacts"
        )

        # This is a little hacky as we have to get everything in a gather operation
        # We have to pass these parameters in as they'll get reassigned to the latest values,
        # as python is weird with closures
        async def load_dag_template(
            dag_template=dag_template, code_artifacts_out=code_artifacts_out, nodes_out=nodes_out
        ) -> Optional[DAGTemplateOutWithData]:
            if dag_template.code_log_store == "none":
                return None
            # TODO -- assert that the blob store matches he one we have available
            code_log = await blob_store.read_obj(dag_template.code_log_url)
            return DAGTemplateOutWithData(
                **dag_template.dict(),
                # TODO -- fix this -- this is due to something weird with the ID names in from_orm
                code_artifacts=code_artifacts_out,
                nodes=nodes_out,
                code=code_log,
            )

        out.append(load_dag_template())
    final_result = list(await asyncio.gather(*out))
    return final_result


# This is due to django ninja being weird
# TODO -- find the right way to do this so we can have the same endpoint prefix
@router.put(
    "/v1/update_dag_templates/{dag_template_id}",
    response=DAGTemplateOut,
    tags=["projects", "templates"],
)
@permission(user_can_update_dag_template)
async def update_dag_template(
    request, dag_template_id: int, dag_template: DAGTemplateUpdate
) -> DAGTemplateOut:
    existing_template = await DAGTemplate.objects.aget(id=dag_template_id)
    existing_template.is_active = dag_template.is_active
    await existing_template.asave()
    return DAGTemplateOut.from_orm(existing_template)
