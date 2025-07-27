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

from django.db import models
from django.utils.translation import gettext as _
from trackingserver_auth.models import User
from trackingserver_base.models import ArrayField as ArrayField
from trackingserver_base.models import GenericAttribute, TimeStampedModel
from trackingserver_template.models import DAGTemplate


class ExecutionStatus(models.TextChoices):
    """Represents the status of a DAG run"""

    RUNNING = "RUNNING", _("RUNNING")
    SUCCESS = "SUCCESS", _("SUCCESS")
    FAILURE = "FAILURE", _("FAILURE")
    UNINITIALIZED = "UNINITIALIZED", _("UNINITIALIZED")


class DAGRun(TimeStampedModel):
    """Represents a run of a DAG. This is a single execution of a DAG, and it is
    uniquely identified by the DAG template, the code version, and the run ID.
    """

    dag_template = models.ForeignKey(DAGTemplate, on_delete=models.SET_NULL, null=True)
    run_start_time = models.DateTimeField(null=True)
    run_end_time = models.DateTimeField(null=True)
    run_status = models.CharField(max_length=255, choices=ExecutionStatus.choices)
    tags = models.JSONField()
    launched_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, default=None)
    inputs = models.JSONField()
    outputs = ArrayField(models.CharField())


class NodeRun(TimeStampedModel):
    """Represents a run of a node. This is a single execution of a node, and it is
    uniquely identified by the DAG run, the node name, and the run ID.
    """

    # Indexed by two foreign keys:
    dag_run = models.ForeignKey(DAGRun, on_delete=models.SET_NULL, null=True)

    # TODO -- consider not indexing on this
    # We'll likely not join on this, and it's not clear that we'll need to
    node_template_name = models.CharField(max_length=255, db_index=True)
    # THe realized name of the node -- this has to be unique among all nodes in the dag run
    node_name = models.CharField()
    # The realized dependencies of the node
    # TODO -- conside making this a mapping from name to realized name(s)?
    # For now this is clear enough...
    realized_dependencies = ArrayField(models.CharField(), null=True)

    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    status = models.CharField(max_length=15, choices=ExecutionStatus.choices)

    class Meta:
        unique_together = ("dag_run", "node_name")


class NodeRunAttribute(GenericAttribute):
    class AttributeRoles(models.TextChoices):
        result_summary = "result_summary", _("result_summary")
        error = "error", _("error")
        resource_utilization = "resource_utilization", _("resource_utilization")
        artifact_link = "artifact_link", _("artifact_link")
        logs = "logs", _("logs")

    # Attributes for a node run
    # Any micro/macro orchestration system could include:
    #    > System performance profiling information (memory, CPU, GPU, etc...)
    #        > name: system_profiling_results
    #        > type: system_profiling_results
    #        > schema_version: 0.0.1
    #        > value: {"CPU_usage" : ..., "GPU_usage" : ..., "memory_usage" : ...} (TBD)
    #    > Links to run views (E.G. airflow, etc...)
    #        > name: airflow_run_link
    #        > type: url
    #        > schema_version: 1
    #        > value: "https://..."
    #    > Summary data
    #        > name: output_summary
    #        > type: dagworks_describe
    #        > schema_version: 2
    #        > value: ... (TBD)
    #    > Logs
    #        > name: logs
    #        > type: log_data
    #        > schema_version: 2
    #        > value: {lines: [...], level: "info"} (TBD)
    #    > Artifacts that a node created, etc...
    #        > name: saved_artifact
    #        > type: artifact_spec
    #        > schema_version: 2
    #        > value: {"source" : "s3", key: ..., bucket: ..., metadata: ...}
    # node_run = models.ForeignKey(NodeRun, on_delete=models.SET_NULL, null=True)
    # TODO -- consider adding dag_run
    dag_run = models.ForeignKey(DAGRun, on_delete=models.SET_NULL, null=True)
    node_name = models.CharField(max_length=255, db_index=True)
    attribute_role = models.CharField(choices=AttributeRoles.choices)

    class Meta:
        unique_together = ("name", "node_name", "dag_run")
