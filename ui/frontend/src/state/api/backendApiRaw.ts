// Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.

import { emptySplitApi as api } from "./emptyApi";
const injectedRtkApi = api.injectEndpoints({
  endpoints: (build) => ({
    trackingserverBaseApiGetAttributesType: build.query<
      TrackingserverBaseApiGetAttributesTypeApiResponse,
      TrackingserverBaseApiGetAttributesTypeApiArg
    >({
      query: () => ({ url: `/api/v1/metadata/attributes/schema` }),
    }),
    trackingserverBaseApiGetCodeVersionTypes: build.query<
      TrackingserverBaseApiGetCodeVersionTypesApiResponse,
      TrackingserverBaseApiGetCodeVersionTypesApiArg
    >({
      query: () => ({ url: `/api/v1/metadata/code_versions/schema` }),
    }),
    trackingserverBaseApiGetNodeMetadataTypes: build.query<
      TrackingserverBaseApiGetNodeMetadataTypesApiResponse,
      TrackingserverBaseApiGetNodeMetadataTypesApiArg
    >({
      query: () => ({ url: `/api/v1/metadata/node_metadata/schema` }),
    }),
    trackingserverBaseApiHealthCheck: build.query<
      TrackingserverBaseApiHealthCheckApiResponse,
      TrackingserverBaseApiHealthCheckApiArg
    >({
      query: () => ({ url: `/api/v1/health` }),
    }),
    trackingserverAuthApiPhoneHome: build.query<
      TrackingserverAuthApiPhoneHomeApiResponse,
      TrackingserverAuthApiPhoneHomeApiArg
    >({
      query: () => ({ url: `/api/v1/phone_home` }),
    }),
    trackingserverAuthApiWhoami: build.query<
      TrackingserverAuthApiWhoamiApiResponse,
      TrackingserverAuthApiWhoamiApiArg
    >({
      query: () => ({ url: `/api/v1/whoami` }),
    }),
    trackingserverAuthApiCreateApiKey: build.mutation<
      TrackingserverAuthApiCreateApiKeyApiResponse,
      TrackingserverAuthApiCreateApiKeyApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/auth/api_key`,
        method: "POST",
        body: queryArg.apiKeyIn,
      }),
    }),
    trackingserverAuthApiGetApiKeys: build.query<
      TrackingserverAuthApiGetApiKeysApiResponse,
      TrackingserverAuthApiGetApiKeysApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/api_keys`,
        params: { limit: queryArg.limit },
      }),
    }),
    trackingserverAuthApiDeleteApiKey: build.mutation<
      TrackingserverAuthApiDeleteApiKeyApiResponse,
      TrackingserverAuthApiDeleteApiKeyApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/api_key/${queryArg.apiKeyId}`,
        method: "DELETE",
      }),
    }),
    trackingserverProjectsApiCreateProject: build.mutation<
      TrackingserverProjectsApiCreateProjectApiResponse,
      TrackingserverProjectsApiCreateProjectApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/projects`,
        method: "POST",
        body: queryArg.projectIn,
      }),
    }),
    trackingserverProjectsApiGetProjects: build.query<
      TrackingserverProjectsApiGetProjectsApiResponse,
      TrackingserverProjectsApiGetProjectsApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/projects`,
        params: {
          attribute_types: queryArg.attributeTypes,
          limit: queryArg.limit,
          offset: queryArg.offset,
        },
      }),
    }),
    trackingserverProjectsApiGetProjectById: build.query<
      TrackingserverProjectsApiGetProjectByIdApiResponse,
      TrackingserverProjectsApiGetProjectByIdApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/projects/${queryArg.projectId}`,
        params: { attribute_types: queryArg.attributeTypes },
      }),
    }),
    trackingserverProjectsApiUpdateProject: build.mutation<
      TrackingserverProjectsApiUpdateProjectApiResponse,
      TrackingserverProjectsApiUpdateProjectApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/projects/${queryArg.projectId}`,
        method: "PUT",
        body: queryArg.bodyParams,
      }),
    }),
    trackingserverTemplateApiCreateDagTemplate: build.mutation<
      TrackingserverTemplateApiCreateDagTemplateApiResponse,
      TrackingserverTemplateApiCreateDagTemplateApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/dag_templates`,
        method: "POST",
        body: queryArg.dagTemplateIn,
        params: { project_id: queryArg.projectId },
      }),
    }),
    trackingserverTemplateApiDagTemplateExists: build.query<
      TrackingserverTemplateApiDagTemplateExistsApiResponse,
      TrackingserverTemplateApiDagTemplateExistsApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/dag_templates/exists/`,
        params: {
          dag_hash: queryArg.dagHash,
          code_hash: queryArg.codeHash,
          dag_name: queryArg.dagName,
          project_id: queryArg.projectId,
        },
      }),
    }),
    trackingserverTemplateApiGetLatestDagTemplates: build.query<
      TrackingserverTemplateApiGetLatestDagTemplatesApiResponse,
      TrackingserverTemplateApiGetLatestDagTemplatesApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/dag_templates/latest/`,
        params: {
          project_id: queryArg.projectId,
          limit: queryArg.limit,
          offset: queryArg.offset,
        },
      }),
    }),
    trackingserverTemplateApiGetDagTemplateCatalog: build.query<
      TrackingserverTemplateApiGetDagTemplateCatalogApiResponse,
      TrackingserverTemplateApiGetDagTemplateCatalogApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/dag_templates/catalog/`,
        params: {
          project_id: queryArg.projectId,
          offset: queryArg.offset,
          limit: queryArg.limit,
        },
      }),
    }),
    trackingserverTemplateApiGetFullDagTemplates: build.query<
      TrackingserverTemplateApiGetFullDagTemplatesApiResponse,
      TrackingserverTemplateApiGetFullDagTemplatesApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/dag_templates/${queryArg.dagTemplateIds}`,
      }),
    }),
    trackingserverTemplateApiUpdateDagTemplate: build.mutation<
      TrackingserverTemplateApiUpdateDagTemplateApiResponse,
      TrackingserverTemplateApiUpdateDagTemplateApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/update_dag_templates/${queryArg.dagTemplateId}`,
        method: "PUT",
        body: queryArg.dagTemplateUpdate,
      }),
    }),
    trackingserverRunTrackingApiCreateDagRun: build.mutation<
      TrackingserverRunTrackingApiCreateDagRunApiResponse,
      TrackingserverRunTrackingApiCreateDagRunApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/dag_runs`,
        method: "POST",
        body: queryArg.dagRunIn,
        params: { dag_template_id: queryArg.dagTemplateId },
      }),
    }),
    trackingserverRunTrackingApiGetLatestDagRuns: build.query<
      TrackingserverRunTrackingApiGetLatestDagRunsApiResponse,
      TrackingserverRunTrackingApiGetLatestDagRunsApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/dag_runs/latest/`,
        params: {
          project_id: queryArg.projectId,
          dag_template_id: queryArg.dagTemplateId,
          limit: queryArg.limit,
          offset: queryArg.offset,
        },
      }),
    }),
    trackingserverRunTrackingApiGetDagRuns: build.query<
      TrackingserverRunTrackingApiGetDagRunsApiResponse,
      TrackingserverRunTrackingApiGetDagRunsApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/dag_runs/${queryArg.dagRunIds}`,
        params: { attr: queryArg.attr },
      }),
    }),
    trackingserverRunTrackingApiUpdateDagRun: build.mutation<
      TrackingserverRunTrackingApiUpdateDagRunApiResponse,
      TrackingserverRunTrackingApiUpdateDagRunApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/dag_runs/${queryArg.dagRunId}/`,
        method: "PUT",
        body: queryArg.dagRunUpdate,
      }),
    }),
    trackingserverRunTrackingApiBulkLog: build.mutation<
      TrackingserverRunTrackingApiBulkLogApiResponse,
      TrackingserverRunTrackingApiBulkLogApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/dag_runs_bulk`,
        method: "PUT",
        body: queryArg.dagRunsBulkRequest,
        params: { dag_run_id: queryArg.dagRunId },
      }),
    }),
    trackingserverRunTrackingApiGetNodeRunForDags: build.query<
      TrackingserverRunTrackingApiGetNodeRunForDagsApiResponse,
      TrackingserverRunTrackingApiGetNodeRunForDagsApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/node_runs/by_run_ids/${queryArg.dagRunIds}`,
        params: { node_name: queryArg.nodeName },
      }),
    }),
    trackingserverRunTrackingApiGetLatestTemplateRuns: build.query<
      TrackingserverRunTrackingApiGetLatestTemplateRunsApiResponse,
      TrackingserverRunTrackingApiGetLatestTemplateRunsApiArg
    >({
      query: (queryArg) => ({
        url: `/api/v1/node_runs/${queryArg.nodeTemplateName}`,
        params: {
          project_id: queryArg.projectId,
          limit: queryArg.limit,
          offset: queryArg.offset,
        },
      }),
    }),
  }),
  overrideExisting: false,
});
export { injectedRtkApi as backendApi };
export type TrackingserverBaseApiGetAttributesTypeApiResponse =
  /** status 200 OK */ AllAttributeTypes;
export type TrackingserverBaseApiGetAttributesTypeApiArg = void;
export type TrackingserverBaseApiGetCodeVersionTypesApiResponse =
  /** status 200 OK */ AllCodeVersionTypes;
export type TrackingserverBaseApiGetCodeVersionTypesApiArg = void;
export type TrackingserverBaseApiGetNodeMetadataTypesApiResponse =
  /** status 200 OK */ AllNodeMetadataTypes;
export type TrackingserverBaseApiGetNodeMetadataTypesApiArg = void;
export type TrackingserverBaseApiHealthCheckApiResponse =
  /** status 200 OK */ boolean;
export type TrackingserverBaseApiHealthCheckApiArg = void;
export type TrackingserverAuthApiPhoneHomeApiResponse =
  /** status 200 OK */ PhoneHomeResult;
export type TrackingserverAuthApiPhoneHomeApiArg = void;
export type TrackingserverAuthApiWhoamiApiResponse =
  /** status 200 OK */ WhoAmIResult;
export type TrackingserverAuthApiWhoamiApiArg = void;
export type TrackingserverAuthApiCreateApiKeyApiResponse =
  /** status 200 OK */ string;
export type TrackingserverAuthApiCreateApiKeyApiArg = {
  apiKeyIn: ApiKeyIn;
};
export type TrackingserverAuthApiGetApiKeysApiResponse =
  /** status 200 OK */ ApiKeyOut[];
export type TrackingserverAuthApiGetApiKeysApiArg = {
  limit?: number;
};
export type TrackingserverAuthApiDeleteApiKeyApiResponse = unknown;
export type TrackingserverAuthApiDeleteApiKeyApiArg = {
  apiKeyId: number;
};
export type TrackingserverProjectsApiCreateProjectApiResponse =
  /** status 200 OK */ ProjectOut;
export type TrackingserverProjectsApiCreateProjectApiArg = {
  projectIn: ProjectIn;
};
export type TrackingserverProjectsApiGetProjectsApiResponse =
  /** status 200 OK */ ProjectOutWithAttributes[];
export type TrackingserverProjectsApiGetProjectsApiArg = {
  attributeTypes?: string | null;
  limit?: number;
  offset?: number;
};
export type TrackingserverProjectsApiGetProjectByIdApiResponse =
  /** status 200 OK */ ProjectOutWithAttributes | null;
export type TrackingserverProjectsApiGetProjectByIdApiArg = {
  projectId: number;
  attributeTypes?: string | null;
};
export type TrackingserverProjectsApiUpdateProjectApiResponse =
  /** status 200 OK */ ProjectOut;
export type TrackingserverProjectsApiUpdateProjectApiArg = {
  projectId: number;
  bodyParams: {
    project: ProjectUpdate;
    attributes?: ProjectAttributeIn[];
  };
};
export type TrackingserverTemplateApiCreateDagTemplateApiResponse =
  /** status 200 OK */ DagTemplateOut;
export type TrackingserverTemplateApiCreateDagTemplateApiArg = {
  projectId: number;
  dagTemplateIn: DagTemplateIn;
};
export type TrackingserverTemplateApiDagTemplateExistsApiResponse =
  /** status 200 OK */ DagTemplateOut | null;
export type TrackingserverTemplateApiDagTemplateExistsApiArg = {
  dagHash: string;
  codeHash: string;
  dagName: string;
  projectId: number;
};
export type TrackingserverTemplateApiGetLatestDagTemplatesApiResponse =
  /** status 200 OK */ DagTemplateOut[];
export type TrackingserverTemplateApiGetLatestDagTemplatesApiArg = {
  projectId: number;
  limit?: number;
  offset?: number;
};
export type TrackingserverTemplateApiGetDagTemplateCatalogApiResponse =
  /** status 200 OK */ CatalogResponse;
export type TrackingserverTemplateApiGetDagTemplateCatalogApiArg = {
  projectId?: number;
  offset?: number;
  limit?: number;
};
export type TrackingserverTemplateApiGetFullDagTemplatesApiResponse =
  /** status 200 OK */ DagTemplateOutWithData[];
export type TrackingserverTemplateApiGetFullDagTemplatesApiArg = {
  dagTemplateIds: string;
};
export type TrackingserverTemplateApiUpdateDagTemplateApiResponse =
  /** status 200 OK */ DagTemplateOut;
export type TrackingserverTemplateApiUpdateDagTemplateApiArg = {
  dagTemplateId: number;
  dagTemplateUpdate: DagTemplateUpdate;
};
export type TrackingserverRunTrackingApiCreateDagRunApiResponse =
  /** status 200 OK */ DagRunOut;
export type TrackingserverRunTrackingApiCreateDagRunApiArg = {
  dagTemplateId: number;
  dagRunIn: DagRunIn;
};
export type TrackingserverRunTrackingApiGetLatestDagRunsApiResponse =
  /** status 200 OK */ DagRunOut[];
export type TrackingserverRunTrackingApiGetLatestDagRunsApiArg = {
  projectId?: number;
  dagTemplateId?: number;
  limit?: number;
  offset?: number;
};
export type TrackingserverRunTrackingApiGetDagRunsApiResponse =
  /** status 200 OK */ DagRunOutWithData[];
export type TrackingserverRunTrackingApiGetDagRunsApiArg = {
  dagRunIds: string;
  attr?: string[];
};
export type TrackingserverRunTrackingApiUpdateDagRunApiResponse =
  /** status 200 OK */ DagRunOut;
export type TrackingserverRunTrackingApiUpdateDagRunApiArg = {
  dagRunId: number;
  dagRunUpdate: DagRunUpdate;
};
export type TrackingserverRunTrackingApiBulkLogApiResponse = unknown;
export type TrackingserverRunTrackingApiBulkLogApiArg = {
  dagRunId: number;
  dagRunsBulkRequest: DagRunsBulkRequest;
};
export type TrackingserverRunTrackingApiGetNodeRunForDagsApiResponse =
  /** status 200 OK */ (NodeRunOutWithAttributes | null)[];
export type TrackingserverRunTrackingApiGetNodeRunForDagsApiArg = {
  dagRunIds: string;
  nodeName: string;
};
export type TrackingserverRunTrackingApiGetLatestTemplateRunsApiResponse =
  /** status 200 OK */ CatalogZoomResponse;
export type TrackingserverRunTrackingApiGetLatestTemplateRunsApiArg = {
  nodeTemplateName: string;
  projectId: number;
  limit?: number;
  offset?: number;
};
export type AttributeDocumentationLoom1 = {
  id: string;
};
export type AttributePrimitive1 = {
  type: string;
  value: string;
};
export type AttributeUnsupported1 = {
  action?: string | null;
  unsupported_type?: string | null;
};
export type PandasDescribeNumericColumn = {
  count: number;
  mean: number;
  min: number;
  max: number;
  std: number;
  q_25_percent: number;
  q_50_percent: number;
  q_75_percent: number;
  dtype: string;
};
export type PandasDescribeCategoricalColumn = {
  count: number | null;
  unique: number;
  top: any;
  freq: number | null;
};
export type AttributePandasDescribe1 = {
  [key: string]: PandasDescribeNumericColumn | PandasDescribeCategoricalColumn;
};
export type AttributeError1 = {
  stack_trace: string[];
};
export type AttributeDict1 = {
  type: string;
  value: string;
};
export type AttributeDict2 = {
  type: string;
  value: object;
};
export type DwDescribeV003UnhandledColumnStatistics = {
  name: string;
  pos: number;
  data_type: string;
  count: number;
  missing: number;
  base_data_type: string;
};
export type DwDescribeV003BooleanColumnStatistics = {
  name: string;
  pos: number;
  data_type: string;
  count: number;
  missing: number;
  base_data_type: string;
  zeros: number;
};
export type DwDescribeV003NumericColumnStatistics = {
  name: string;
  pos: number;
  data_type: string;
  count: number;
  missing: number;
  base_data_type: string;
  zeros: number;
  min: number;
  max: number;
  mean: number;
  std: number;
  quantiles: {
    [key: string]: number;
  };
  histogram: {
    [key: string]: number;
  };
};
export type DwDescribeV003DatetimeColumnStatistics = {
  name: string;
  pos: number;
  data_type: string;
  count: number;
  missing: number;
  base_data_type: string;
};
export type DwDescribeV003CategoryColumnStatistics = {
  name: string;
  pos: number;
  data_type: string;
  count: number;
  missing: number;
  base_data_type: string;
  empty: number;
  domain: {
    [key: string]: number;
  };
  top_value: string;
  top_freq: number;
  unique: number;
};
export type DwDescribeV003StringColumnStatistics = {
  name: string;
  pos: number;
  data_type: string;
  count: number;
  missing: number;
  base_data_type: string;
  avg_str_len: number;
  std_str_len: number;
  empty: number;
};
export type AttributeDagworksDescribe3 = {
  [key: string]:
    | DwDescribeV003UnhandledColumnStatistics
    | DwDescribeV003BooleanColumnStatistics
    | DwDescribeV003NumericColumnStatistics
    | DwDescribeV003DatetimeColumnStatistics
    | DwDescribeV003CategoryColumnStatistics
    | DwDescribeV003StringColumnStatistics;
};
export type AttributeHTML1 = {
  html: string;
};

export type ColSchema = {
  name: string;
  type: string;
  nullable: boolean;
  metadata: object;
};
export type AttributeSchema1 = {
  [key: string]: ColSchema;
};
export type AllAttributeTypes = {
  documentation_loom__1: AttributeDocumentationLoom1;
  primitive__1: AttributePrimitive1;
  unsupported__1: AttributeUnsupported1;
  pandas_describe__1: AttributePandasDescribe1;
  error__1: AttributeError1;
  dict__1: AttributeDict1;
  dict__2: AttributeDict2;
  dagworks_describe__3: AttributeDagworksDescribe3;
  html__1: AttributeHTML1;
  schema__1: AttributeSchema1;
};
export type CodeVersionGit1 = {
  git_hash: string;
  git_repo: string;
  git_branch: string;
  committed: boolean;
};
export type AllCodeVersionTypes = {
  git__1: CodeVersionGit1;
};
export type NodeMetadataPythonType1 = {
  type_name: string;
};
export type AllNodeMetadataTypes = {
  python_type__1: NodeMetadataPythonType1;
};
export type PhoneHomeResult = {
  success: boolean;
  message: string;
};
export type UserOut = {
  id?: number | null;
  email: string;
  first_name: string;
  last_name: string;
};
export type TeamOut = {
  id?: number | null;
  name: string;
  auth_provider_type: string;
  auth_provider_organization_id: string;
};
export type WhoAmIResult = {
  user: UserOut;
  teams: TeamOut[];
};
export type ApiKeyIn = {
  name: string;
};
export type ApiKeyOut = {
  id?: number | null;
  key_name: string;
  key_start: string;
  is_active?: boolean;
  created_at: string;
  updated_at: string;
};
export type VisibilityOut = {
  users_visible: UserOut[];
  users_writable: UserOut[];
  teams_visible: TeamOut[];
  teams_writable: TeamOut[];
};
export type ProjectOut = {
  name: string;
  description: string;
  tags: {
    [key: string]: string;
  };
  id: number;
  role?: string;
  visibility: VisibilityOut;
  created_at: string;
  updated_at: string;
};
export type Visibility = {
  user_ids_visible: (string | number)[];
  team_ids_visible: number[];
  team_ids_writable: number[];
  user_ids_writable: (string | number)[];
};
export type ProjectAttributeIn = {
  name: string;
  type: string;
  schema_version: number;
  value: object;
};
export type ProjectIn = {
  name: string;
  description: string;
  tags: {
    [key: string]: string;
  };
  visibility: Visibility;
  attributes?: ProjectAttributeIn[];
};
export type ProjectAttributeOut = {
  name: string;
  type: string;
  schema_version: number;
  value: object;
  id?: number | null;
  project?: number | null;
};
export type ProjectOutWithAttributes = {
  name: string;
  description: string;
  tags: {
    [key: string]: string;
  };
  id: number;
  role?: string;
  visibility: VisibilityOut;
  created_at: string;
  updated_at: string;
  attributes: ProjectAttributeOut[];
};
export type ProjectUpdate = {
  name?: string | null;
  description?: string | null;
  tags?: {
    [key: string]: string;
  } | null;
  visibility?: Visibility | null;
};
export type DagTemplateOut = {
  id?: number | null;
  created_at: string;
  updated_at: string;
  project?: number | null;
  name: string;
  template_type: string;
  config?: object | null;
  dag_hash: string;
  is_active?: boolean;
  tags?: object | null;
  code_hash: string;
  code_version_info_type: string;
  code_version_info?: object | null;
  code_version_info_schema?: number | null;
  code_log_store: string;
  code_log_url?: string | null;
  code_log_schema_version?: number | null;
};
export type NodeTemplateIn = {
  code_artifact_pointers: string[];
  name: string;
  dependencies?: any[] | null;
  dependency_specs?: any[] | null;
  dependency_specs_type?: string | null;
  dependency_specs_schema_version?: number | null;
  output?: object | null;
  output_type?: string | null;
  output_schema_version?: number | null;
  documentation?: string | null;
  tags?: object | null;
  classifications: any[];
};
export type CodeArtifactIn = {
  dag_template_id?: number | null;
  name: string;
  type: string;
  path: string;
  start: number;
  end: number;
  url: string;
};
export type File = {
  path: string;
  contents: string;
};
export type CodeLog = {
  files: File[];
};
export type DagTemplateIn = {
  nodes: NodeTemplateIn[];
  code_artifacts: CodeArtifactIn[];
  code_log: CodeLog;
  name: string;
  template_type: string;
  config?: object | null;
  dag_hash: string;
  tags?: object | null;
  code_hash: string;
  code_version_info_type: string;
  code_version_info?: object | null;
  code_version_info_schema?: number | null;
};
export type NodeTemplateOut = {
  dag_template_id: number;
  primary_code_artifact?: string | null;
  id?: number | null;
  created_at: string;
  updated_at: string;
  name: string;
  dag_template?: number | null;
  dependencies?: any[] | null;
  dependency_specs?: any[] | null;
  dependency_specs_type?: string | null;
  dependency_specs_schema_version?: number | null;
  output?: object | null;
  output_type?: string | null;
  output_schema_version?: number | null;
  documentation?: string | null;
  tags?: object | null;
  classifications: any[];
  code_artifacts: number[];
};
export type CodeArtifactOut = {
  id?: number | null;
  created_at: string;
  updated_at: string;
  dag_template?: number | null;
  name: string;
  type: string;
  path: string;
  start: number;
  end: number;
  url: string;
};
export type CatalogResponse = {
  nodes: NodeTemplateOut[];
  code_artifacts: CodeArtifactOut[];
};
export type DagTemplateOutWithData = {
  id?: number | null;
  created_at: string;
  updated_at: string;
  project?: number | null;
  name: string;
  template_type: string;
  config?: object | null;
  dag_hash: string;
  is_active?: boolean;
  tags?: object | null;
  code_hash: string;
  code_version_info_type: string;
  code_version_info?: object | null;
  code_version_info_schema?: number | null;
  code_log_store: string;
  code_log_url?: string | null;
  code_log_schema_version?: number | null;
  nodes: NodeTemplateOut[];
  code_artifacts: CodeArtifactOut[];
  code: CodeLog | null;
};
export type DagTemplateUpdate = {
  is_active?: boolean;
};
export type DagRunOut = {
  dag_template_id: number;
  username_resolved?: string | null;
  id?: number | null;
  created_at: string;
  updated_at: string;
  dag_template?: number | null;
  run_start_time?: string | null;
  run_end_time?: string | null;
  run_status: string;
  tags: object;
  launched_by?: number | null;
  inputs: object;
  outputs: any[];
};
export type DagRunIn = {
  run_start_time?: string | null;
  run_end_time?: string | null;
  run_status: string;
  tags: object;
  launched_by_id?: number | null;
  inputs: object;
  outputs: any[];
};
export type NodeRunAttributeOut = {
  dag_run_id: number;
  id?: number | null;
  created_at: string;
  updated_at: string;
  name: string;
  type: string;
  schema_version: number;
  value: object;
  dag_run?: number | null;
  node_name: string;
  attribute_role: string;
};
export type NodeRunOutWithAttributes = {
  id?: number | null;
  created_at: string;
  updated_at: string;
  dag_run?: number | null;
  node_template_name: string;
  node_name: string;
  realized_dependencies?: any[] | null;
  start_time?: string | null;
  end_time?: string | null;
  status: string;
  attributes: NodeRunAttributeOut[];
  dag_run_id: number;
};
export type DagRunOutWithData = {
  dag_template_id: number;
  username_resolved?: string | null;
  id?: number | null;
  created_at: string;
  updated_at: string;
  dag_template?: number | null;
  run_start_time?: string | null;
  run_end_time?: string | null;
  run_status: string;
  tags: object;
  launched_by?: number | null;
  inputs: object;
  outputs: any[];
  node_runs: NodeRunOutWithAttributes[];
};
export type DagRunUpdate = {
  run_status: "RUNNING" | "SUCCESS" | "FAILURE" | "UNINITIALIZED";
  run_end_time: string;
  upsert_tags?: object | null;
};
export type NodeRunAttributeIn = {
  name: string;
  type: string;
  schema_version: number;
  value: object;
  node_name: string;
  attribute_role: string;
};
export type NodeRunIn = {
  node_template_name: string;
  node_name: string;
  realized_dependencies?: any[] | null;
  start_time?: string | null;
  end_time?: string | null;
  status: string;
};
export type DagRunsBulkRequest = {
  attributes: NodeRunAttributeIn[];
  task_updates: NodeRunIn[];
};
export type NodeRunOutWithExtraData = {
  id?: number | null;
  created_at: string;
  updated_at: string;
  dag_run?: number | null;
  node_template_name: string;
  node_name: string;
  realized_dependencies?: any[] | null;
  start_time?: string | null;
  end_time?: string | null;
  status: string;
  dag_template_id: number;
  dag_run_id: number;
};
export type CatalogZoomResponse = {
  node_runs: NodeRunOutWithExtraData[];
  node_templates: NodeTemplateOut[];
  code_artifacts: CodeArtifactOut[];
};
export const {
  useTrackingserverBaseApiGetAttributesTypeQuery,
  useTrackingserverBaseApiGetCodeVersionTypesQuery,
  useTrackingserverBaseApiGetNodeMetadataTypesQuery,
  useTrackingserverBaseApiHealthCheckQuery,
  useTrackingserverAuthApiPhoneHomeQuery,
  useTrackingserverAuthApiWhoamiQuery,
  useTrackingserverAuthApiCreateApiKeyMutation,
  useTrackingserverAuthApiGetApiKeysQuery,
  useTrackingserverAuthApiDeleteApiKeyMutation,
  useTrackingserverProjectsApiCreateProjectMutation,
  useTrackingserverProjectsApiGetProjectsQuery,
  useTrackingserverProjectsApiGetProjectByIdQuery,
  useTrackingserverProjectsApiUpdateProjectMutation,
  useTrackingserverTemplateApiCreateDagTemplateMutation,
  useTrackingserverTemplateApiDagTemplateExistsQuery,
  useTrackingserverTemplateApiGetLatestDagTemplatesQuery,
  useTrackingserverTemplateApiGetDagTemplateCatalogQuery,
  useTrackingserverTemplateApiGetFullDagTemplatesQuery,
  useTrackingserverTemplateApiUpdateDagTemplateMutation,
  useTrackingserverRunTrackingApiCreateDagRunMutation,
  useTrackingserverRunTrackingApiGetLatestDagRunsQuery,
  useTrackingserverRunTrackingApiGetDagRunsQuery,
  useTrackingserverRunTrackingApiUpdateDagRunMutation,
  useTrackingserverRunTrackingApiBulkLogMutation,
  useTrackingserverRunTrackingApiGetNodeRunForDagsQuery,
  useTrackingserverRunTrackingApiGetLatestTemplateRunsQuery,
} = injectedRtkApi;
