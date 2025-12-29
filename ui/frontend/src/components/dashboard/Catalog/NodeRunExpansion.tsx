/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

/**
 * Table view of an expanded node run.
 * TODO -- unify this with the table view of a run in the runs page
 * I'm implementing this first and just copying the code over, then I'll be moving this and using it.
 */

import {
  CatalogNodeRun,
  CodeArtifact,
  NodeMetadataPythonType1,
  NodeTemplate,
  RunStatusType,
  getNodeOutputType,
  useNodeRunsByTemplateAndProject,
} from "../../../state/api/friendlyApi";
import { GenericTable } from "../../common/GenericTable";
import { RunLink, VersionLink } from "../../common/CommonLinks";
import { RunStatus } from "../Runs/Status";
import ReactTimeAgo from "react-time-ago";
import { adjustStatusForDuration, parsePythonType } from "../../../utils";
import { FunctionDisplay, RowToDisplay } from "./SearchTable";
import { ErrorPage } from "../../common/Error";
import { Loading } from "../../common/Loading";
import { RunDurationChart } from "../../common/RunDurationChart";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { DurationDisplay } from "../../common/Datetime";

type NodeRunAndTemplate = CatalogNodeRun & {
  nodeTemplateData?: NodeTemplate;
  projectId?: number;
  codeArtifact?: CodeArtifact;
};
export const columns = [
  {
    displayName: "Run",
    Render: (data: NodeRunAndTemplate) => {
      // TODO -- hide this for subrows...
      return (
        <div className="w-min">
          <RunLink
            projectId={data.projectId as number}
            runId={data.dag_run_id as number}
            setHighlightedRun={() => void 0}
            highlightedRun={null}
            taskName={data.node_name}
          ></RunLink>
        </div>
      );
    },
  },
  // {
  //   displayName: "Node",
  //   Render: (nodeRun: CatalogNodeRun) => {
  //     // TODO -- hide this for subrows...
  //     return (
  //       <div className="w-max">
  //         <span className="font-semibold flex flex-row gap-2 items-center">
  //           {nodeRun.node_name}
  //         </span>
  //       </div>
  //     );
  //   },
  // },

  {
    displayName: "Type",
    Render: (data: NodeRunAndTemplate) => {
      const nodeTemplateData = data.nodeTemplateData;
      if (nodeTemplateData === undefined) {
        return <span className="font-semibold">-</span>;
      }
      const pythonType = getNodeOutputType<NodeMetadataPythonType1>(
        nodeTemplateData,
        "NodeMetadataPythonType1"
      );
      if (pythonType === undefined) {
        return <span className="font-semibold">-</span>;
      }
      return (
        <code className="break-words whitespace-pre-wrap">
          {parsePythonType(pythonType)}
        </code>
      );
      // return <span className="font-semibold">{props.nodeName}</span>;
    },
  },
  {
    displayName: "State",
    Render: (nodeRun: NodeRunAndTemplate) => {
      // TODO -- ensure that this is the right type
      let status = nodeRun.status as RunStatusType;
      status = adjustStatusForDuration(
        status,
        nodeRun.start_time || undefined,
        nodeRun.end_time || undefined,
        new Date()
      );
      return <RunStatus status={status} />;
    },
  },
  {
    displayName: "Duration",
    Render: (nodeRun: CatalogNodeRun) => {
      if (
        nodeRun.start_time === undefined ||
        nodeRun.start_time === null ||
        nodeRun.end_time === undefined ||
        nodeRun.end_time === null
      ) {
        return <span className="font-semibold">-</span>;
      }

      // const startMillis = new Date(nodeRun.start_time).getTime();
      // const endMillis = new Date(nodeRun.end_time).getTime();
      // const runTime = (endMillis - startMillis) / 1000;

      // const timeString = runTime.toFixed(3) + "s";
      // return <span className="font-semibold">{timeString}</span>;
      return (
        <DurationDisplay
          startTime={nodeRun.start_time || undefined}
          endTime={nodeRun.end_time || undefined}
          currentTime={new Date()}
        />
      );
    },
  },
  {
    displayName: "",
    Render: (nodeRun: CatalogNodeRun) => {
      // TODO -- ensure that this is the right type
      if (nodeRun.start_time === undefined || nodeRun.start_time === null) {
        return <span className="font-semibold">-</span>;
      }
      return <ReactTimeAgo date={new Date(nodeRun.start_time)} />;
    },
  },
];

export const NodeRunsTable = (props: {
  nodeRuns: CatalogNodeRun[];
  nodeTemplates: NodeTemplate[];
  codeArtifacts: CodeArtifact[];
  projectId: number;
}) => {
  const nodeTemplatesByDAGTemplate = new Map<number, NodeTemplate>();
  const navigate = useNavigate();
  props.nodeTemplates.forEach((nodeTemplate) => {
    const dagTemplate = nodeTemplate.dag_template as number;
    nodeTemplatesByDAGTemplate.set(dagTemplate, nodeTemplate); // One per each DAG run? AT least they'll be the same...
  });
  const [selectedRunIds, setSelectedRunIds] = useState<Set<number>>(new Set());

  const codeArtifactsById = new Map<number, CodeArtifact>();
  props.codeArtifacts.forEach((codeArtifact) => {
    codeArtifactsById.set(codeArtifact.id as number, codeArtifact);
  });

  const data = props.nodeRuns.map((nodeRun) => {
    const nodeTemplate = nodeTemplatesByDAGTemplate.get(
      nodeRun.dag_template_id as number
    );
    const hasCodeArtifact = (nodeTemplate?.code_artifacts || []).length > 0;
    return [
      nodeRun.dag_run?.toString() || "",
      {
        ...nodeRun,
        ...{ nodeTemplateData: nodeTemplate },
        ...{ projectId: props.projectId },
        ...{
          codeArtifact: hasCodeArtifact
            ? codeArtifactsById.get(nodeTemplate?.code_artifacts[0] as number) // TODO -- use multiple code artifacts to link out to multiple...
            : undefined,
        },
      },
    ] as [string, NodeRunAndTemplate];
  });
  return (
    <div className="w-full p-4 bg-dwlightblue/5 flex flex-col -gap-2">
      <div className="flex flex-row justify-end">
        <button
          onClick={() => {
            navigate(
              `/dashboard/project/${props.projectId}/runs/${Array.from(
                selectedRunIds
              ).join(",")}/task/${props.nodeRuns[0]?.node_name}` // This assumes the node names are the same
              // With parallelism this might not be the case
            );
          }}
          type="button"
          disabled={selectedRunIds.size < 1}
          className={`runs-compare rounded bg-dwlightblue px-2 py-1 text-sm font-semibold w-20
            text-white shadow-sm hover:bg-dwlightblue focus-visible:outline
              focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-dwlightblue ${
                selectedRunIds.size < 1 ? "opacity-70" : ""
              }`}
        >
          {selectedRunIds.size >= 2
            ? "Compare"
            : selectedRunIds.size == 1
            ? "View"
            : "Select..."}
        </button>
      </div>
      <GenericTable
        data={data}
        columns={columns}
        dataTypeName={"Version"}
        dataTypeDisplay={(label: string, nodeRun: NodeRunAndTemplate) => (
          <div className="flex flex-row gap-2 items-center">
            <input
              id="comments"
              aria-describedby="comments-description"
              name="comments"
              type="checkbox"
              checked={selectedRunIds.has(nodeRun.dag_run_id as number)}
              onChange={(e) => {
                const newSelectedRunIds = new Set(selectedRunIds);
                if (e.target.checked) {
                  newSelectedRunIds.add(nodeRun.dag_run_id as number);
                } else {
                  newSelectedRunIds.delete(nodeRun.dag_run_id as number);
                }
                setSelectedRunIds(newSelectedRunIds);
              }}
              className="h-4 w-4 rounded border-gray-300 text-dwdarkblue focus:ring-dwdarkblue"
            />
            <VersionLink
              projectId={props.projectId}
              versionId={nodeRun.dag_template_id}
              nodeName={nodeRun.node_name}
            ></VersionLink>
            {nodeRun.codeArtifact && (
              <div className="font-semibold">
                <FunctionDisplay
                  projectId={nodeRun.projectId as number}
                  projectVersionId={nodeRun.dag_template_id as number}
                  code={nodeRun.codeArtifact}
                  justIcon={true}
                />
              </div>
            )}
          </div>
        )}
      ></GenericTable>
    </div>
  );
};

export const NodeRunsView = (props: {
  value: RowToDisplay;
  view: "runtime-chart" | "table" | undefined;
}) => {
  const { node, projectId } = props.value;
  const nodeTemplateName = node.name;
  const lastN = 100; // TODO -- make this configurable/part of the RowToDisplay
  const latestNodeRuns = useNodeRunsByTemplateAndProject({
    nodeTemplateName,
    projectId,
    limit: lastN,
  });
  if (latestNodeRuns.error) {
    return (
      <ErrorPage
        message={`Failed to load node runs for node=${nodeTemplateName} and project=${projectId}`}
      />
    );
  }
  if (
    latestNodeRuns.isLoading ||
    latestNodeRuns.isFetching ||
    latestNodeRuns.isUninitialized
  ) {
    return <Loading />;
  }
  const nodeRuns = latestNodeRuns.data.node_runs || [];
  const nodeTemplates = latestNodeRuns.data.node_templates || [];
  const codeArtifacts = latestNodeRuns.data.code_artifacts || [];
  if (props.view === undefined) {
    return <></>;
  }
  if (nodeRuns.length === 0) {
    return (
      <div className="text-3xl text-gray-300 p-5 bg-gray-50 text-center font-semibold">
        No runs found
      </div>
    );
  }
  if (props.view === "table") {
    return (
      <NodeRunsTable
        nodeRuns={nodeRuns}
        projectId={projectId}
        nodeTemplates={nodeTemplates}
        codeArtifacts={codeArtifacts}
      />
    );
  }
  const nodeRunsSorted = nodeRuns.slice().sort((a, b) => {
    if (
      [a.start_time, b.start_time].some(
        (item) => item === null || item === undefined
      )
    ) {
      return 0;
    }
    return (
      new Date(a.start_time as string).getTime() -
      new Date(b.start_time as string).getTime()
    );
  });

  const runInfo = nodeRunsSorted.map((nodeRun) => {
    return {
      name: nodeRun.node_name as string,
      state: nodeRun.status as RunStatusType,
      runId: nodeRun.dag_run as number,
      duration: [nodeRun.end_time, nodeRun.start_time].some(
        (item) => item === null || item === undefined
      )
        ? undefined
        : (new Date(nodeRun.end_time as string).getTime() -
            new Date(nodeRun.start_time as string).getTime()) /
          1000,
    };
  });
  return <RunDurationChart runInfo={runInfo} w="w-[full]" h="h-[500px]" />;
};
