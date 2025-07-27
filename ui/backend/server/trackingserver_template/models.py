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

from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.translation import gettext as _
from trackingserver_base.models import ArrayField as ArrayField
from trackingserver_base.models import GenericAttribute, TimeStampedModel
from trackingserver_projects.models import Project


class CodeVersion(TimeStampedModel):
    """Represents a version of code -- this is uniquely identified by a hash + version info type"""


class DAGTemplate(TimeStampedModel):
    """This is a template for a DAG. Its become a bit large, and it's quite likely we'll
    want to separate this out at some point int he future. For now, it contains:

    1. Name
    2. DAG Hash
    3. Code Hash

    To find the actual nodes + code artifacts, you have to find associated NodeTemplates
    and they're associated code artifacts. Any code we konw about is stored with the
    DAGTemplate.
    """

    class TemplateType(models.TextChoices):
        HAMILTON = "HAMILTON", _("Hamilton")

    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)

    # DAG templates have a name
    name = models.CharField(max_length=255)

    # the type of the template
    template_type = models.CharField(max_length=255, choices=TemplateType.choices)

    # Any configuration information required to create it
    config = models.JSONField(null=True)

    # Unique dag hash -- this hashes the DAG + config so we only store once
    # This is computed on the user-side -- a merkel hash of the nodes
    dag_hash = models.CharField(max_length=64, validators=[MinLengthValidator(64)], unique=False)
    is_active = models.BooleanField(default=True)
    tags = models.JSONField(null=True)

    class CodeLogStore(models.TextChoices):
        s3 = "s3", _("S3")
        local = "local", _("Local")
        none = "none", _("None")

    class VersionInfo(models.TextChoices):
        GIT = "git", _("Git")
        AD_HOC = "ad_hoc", _("Ad hoc")

    code_hash = models.CharField()

    code_version_info_type = models.CharField(choices=VersionInfo.choices)
    code_version_info = models.JSONField(null=True)
    code_version_info_schema = models.IntegerField(null=True)

    code_log_store = models.CharField(choices=CodeLogStore.choices)

    # Blob store location
    code_log_url = models.CharField(default=None, null=True)  # We allow you not to store code

    # We will handle versions on the server side in case we want to store specific information
    code_log_schema_version = models.IntegerField(null=True)

    class Meta:
        unique_together = ("dag_hash", "code_hash", "name", "project")


class DAGTemplateAttribute(GenericAttribute):
    # In Hamilton's case:
    # > All Availalable Functions
    dag_template = models.ForeignKey(DAGTemplate, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ("name", "dag_template")


class CodeArtifact(TimeStampedModel):
    """Represents a code artifact -- this is a unique code artifact, and it is
    uniquely identified by the code hash and the artifact name.
    """

    dag_template = models.ForeignKey(DAGTemplate, on_delete=models.SET_NULL, null=True)

    class ArtifactType(models.TextChoices):
        PYTHON_FUNCTION = "p_function", _("Function")
        PYTHON_CLASS = "p_class", _("Class")
        PYTHON_MODULE = "p_module", _("Module")
        UNKNOWN = "p_unknown", _("Unknown")

    # The name of the code artifact
    # Note this must be unique within a project version so we can access this
    name = models.CharField()

    # The type of the code artifact
    type = models.CharField(max_length=15, choices=ArtifactType.choices)

    # The path to the code artifact
    path = models.CharField()

    # The start line of the code artifact
    start = models.IntegerField()

    # The end line of the code artifact
    end = models.IntegerField()

    # The URL to the code artifact
    url = models.CharField(max_length=255)


class NodeTemplateCodeArtifactRelation(TimeStampedModel):
    is_primary = models.BooleanField(default=False)
    node_template = models.ForeignKey("NodeTemplate", on_delete=models.SET_NULL, null=True)
    code_artifact = models.ForeignKey("CodeArtifact", on_delete=models.SET_NULL, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["node_template", "is_primary"],
                name="unique_primary",
                condition=models.Q(is_primary=True),
            ),
        ]


class NodeTemplate(TimeStampedModel):
    """Represents a node in a template DAG. This is general -- it doesn't have to have
    depeendencies, etc..., but the more we know the better."""

    class NodeType(models.TextChoices):
        transform = "transform", _("Transform")
        data_saver = "data_saver", _("DataSaver")
        data_loader = "data_loader", _("DataLoader")
        input = "input", _("Input")  # input, not actually run
        placeholder = "placeholder", _("Placeholder")

    # Nodes have a unique name (up to 511 chars)
    # In Hamilton's case, this includes a .-separated namespace
    name = models.CharField(db_index=True)

    # Nodes have a template they belong to -- this is an indexed foreign key
    dag_template = models.ForeignKey(DAGTemplate, on_delete=models.SET_NULL, null=True)

    # Nodes have one or more code artifacts that they use
    # These
    code_artifacts = models.ManyToManyField(
        "CodeArtifact",
        db_index=False,
        through=NodeTemplateCodeArtifactRelation,
        related_name="code_artifacts",
    )

    # nodes have dependencies -- these are references to other nodes, but not handled by the DB
    # This is in case we need to be flexbile
    dependencies = ArrayField(models.CharField(), null=True)

    # Nodes have specs for dependencies to specify types/whatnot
    dependency_specs = ArrayField(models.JSONField(), null=True)
    dependency_specs_type = models.CharField(max_length=63, null=True)
    dependency_specs_schema_version = models.IntegerField(null=True)

    # Nodes have a spec for the output
    # This is nullable in case the output is nothing
    output = models.JSONField(null=True)
    output_type = models.CharField(null=True)
    output_schema_version = models.IntegerField(null=True)

    # all nodes have the capability to have documentation
    documentation = models.TextField(null=True)

    # Any tags the node specifies (arbitrary json)
    # In hamilton's case, this corresponds directly to tags
    tags = models.JSONField(null=True)

    classifications = ArrayField(models.CharField(choices=NodeType.choices))

    class Meta:
        unique_together = ("name", "dag_template")

    def __str__(self):
        return self.name + " in " + str(self.dag_template_id)


# For now let's leave this out
# class TemplateNodeAttribute(GenericAttribute):
#     template_node = models.ForeignKey(TemplateNode, on_delete=models.SET_NULL, null=True)
