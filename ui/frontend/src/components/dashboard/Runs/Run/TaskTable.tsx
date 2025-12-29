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

import { FC, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { HashLink } from "react-router-hash-link";
import { FaRegFileCode } from "react-icons/fa";
import { HiChevronDown, HiChevronUp } from "react-icons/hi";
import { TaskProperty } from "./Run";
import { adjustStatusForDuration, parsePythonType } from "../../../../utils";
import { TbDelta } from "react-icons/tb";
import { RxMagnifyingGlass } from "react-icons/rx";
import VisibilitySensor from "react-visibility-sensor";
import {
  CodeArtifact,
  DAGRunWithData,
  DAGTemplateWithData,
  NodeMetadataPythonType1,
  NodeRunWithAttributes,
  NodeTemplate,
  RunStatusType,
  getNodeOutputType,
} from "../../../../state/api/friendlyApi";
import { RunLink } from "../../../common/CommonLinks";
import { RunStatus } from "../Status";
import { DurationDisplay } from "../../../common/Datetime";

/**
 * This is a mess -- we need to clean this up at some point but I'm just hacking it together now.
 * Luckily, its self-contained.
 *
 * We need to:
 *
 * 1. Get it to work with generic table row
 * 2. Clean up the logic with render props/whatnot -- too much arbitrary data transformation
 * - we should be able to just pass through the code artifacts, node templates, and node runs, and have it work.
 */
type RenderProps = {
  nodeName: string;
  nodeTemplates: (NodeTemplate | undefined)[];
  projectId: number;
  projectVersionIds: number[];
  runIds: number[];
  taskRuns: NodeRunWithAttributes[];
  code: (CodeArtifact | undefined)[];
  statuses: string[];
  summaryRow: boolean;
  isExpanded: boolean;
  navigate: ReturnType<typeof useNavigate>;
  isOutputNodes: boolean[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  inputNodeValues: (any | undefined)[];
  highlightedRun: number | null;
  setHighlightedRun: (runId: number | null) => void;
  toggleExpanded?: (() => void) | undefined;
  isSubrow: boolean;
  currentTime: Date;
};
/**
 * Splits the node name into the task name and the node name. This is a bit of a hack, as we're not storing task-level data.
 * For now its OK as we know there's a "-" in the name to delimit the task name and the node name.
 * We also just assume there's no task if there's no "-" in the name.
 * TODO -- add task name to the node data model.
 * @param templateName
 * @param nodeName
 * @returns
 */
const parseNode = (
  templateName: string,
  nodeName: string
): [string | undefined, string] => {
  // const regex = new RegExp("-" + templateName + "$");
  const nodeNameSplit = nodeName.split("-");
  const lastItemInSplit = nodeNameSplit[nodeNameSplit.length - 1];
  const restOfSplit = nodeNameSplit
    .slice(0, nodeNameSplit.length - 1)
    .join("-");
  // A hack becuase of the naming scheme for a taskless node
  const taskName =
    nodeNameSplit.length === 1 || restOfSplit === lastItemInSplit
      ? undefined
      : restOfSplit;
  return [taskName, lastItemInSplit];
};

const cols = (hasAnyGroupingTask: boolean) => {
  return [
    {
      displayName: "",
      render: (props: RenderProps) => {
        const Icon = props.isExpanded ? HiChevronUp : HiChevronDown;
        return props.toggleExpanded !== undefined ? (
          <div className="flex justify-end align-middle items-center">
            <Icon
              className="hover:scale-125 hover:cursor-pointer text-2xl text-gray-400 mr-1"
              onClick={() => props.toggleExpanded?.()}
            />
          </div>
        ) : (
          <></>
        );
      },
    },
    {
      displayName: "Runs",
      render: (props: RenderProps) => {
        if (props.isExpanded && props.summaryRow) {
          return <></>;
        }

        return (
          <div className="flex flex-row gap-1">
            {props.taskRuns.map((taskRun, i) => (
              <RunLink
                key={i}
                projectId={props.projectId}
                runId={props.runIds[i]}
                highlightedRun={props.highlightedRun}
                setHighlightedRun={props.setHighlightedRun}
              />
            ))}
          </div>
        );
      },
    },

    ...(hasAnyGroupingTask
      ? [
          {
            displayName: "Task",
            render: (props: RenderProps) => {
              // TODO -- hide this for subrows...
              if (props.isSubrow) {
                return <></>;
              }
              const taskName = parseNode(
                props.nodeTemplates[0]?.name || "",
                props.nodeName
              )[0];
              if (taskName === undefined) {
                return <></>;
              }
              return (
                <div className="w-max">
                  <span className="font-semibold flex flex-row gap-2 items-center w-48">
                    {taskName}
                  </span>
                </div>
              );
            },
          },
        ]
      : []),

    {
      displayName: "Node",
      render: (props: RenderProps) => {
        // TODO -- hide this for subrows...
        if (props.isSubrow) {
          return <></>;
        }
        const nodeName = parseNode(
          props.nodeTemplates[0]?.name || "",
          props.nodeName
        )[1];
        return (
          <div className="w-max">
            <span className="font-semibold flex flex-row gap-2 items-center">
              {nodeName}
            </span>
          </div>
        );
      },
    },
    {
      displayName: "Type",
      render: (props: RenderProps) => {
        // TODO -- hide this for subrows...
        if (props.summaryRow && props.isExpanded) {
          return <></>;
        }
        const seenTypes = new Set<string>();
        return (
          <div className="max-w-xs flex flex-row gap-2">
            {props.nodeTemplates.map((nodeTemplate, i) => {
              const nodeType = nodeTemplate
                ? getNodeOutputType<NodeMetadataPythonType1>(
                    nodeTemplate,
                    "NodeMetadataPythonType1"
                  )
                : undefined;
              if (nodeType === undefined || seenTypes.has(nodeType.type_name)) {
                return <></>;
              }
              seenTypes.add(nodeType.type_name);
              const type = parsePythonType(nodeType);
              if (nodeType.type_name === "None") {
                return <></>;
              }
              return (
                <code className="break-words whitespace-pre-wrap" key={i}>
                  {type}
                </code>
              );
            })}
          </div>
        );
        // return <span className="font-semibold">{props.nodeName}</span>;
      },
    },
    {
      displayName: "",
      render: (props: RenderProps) => {
        if (props.summaryRow) {
          // if its the summary row and expanded, show just the node name, no link
          return <></>;
        } else if (props.code[0]) {
          return (
            <HashLink
              className=" hover:underline"
              to={`/dashboard/project/${props.projectId}/version/${
                props.projectVersionIds[0]
              }/code/#${props.code[0].name.replace(".", "_")}`}
            >
              <FaRegFileCode className={`hover:scale-125 text-xl`} />
            </HashLink>
          );
        } else {
          return <></>;
        }
      },
    },
    {
      displayName: "Properties",
      render: (props: RenderProps) => {
        const types = new Set<"input" | "output">();
        const inputNodeValues = props.inputNodeValues.filter((n) => n);
        // const outputNodes = props.isOutputNodes.filter((n) => n);
        if (props.isExpanded && props.summaryRow && props.code.length > 1) {
          return <></>;
        }
        props.isOutputNodes.forEach((isOutputNode, i) => {
          if (isOutputNode) {
            types.add("output");
          } else if (inputNodeValues[i] !== undefined) {
            types.add("input");
          } else {
            // types.add("transform")
          }
        });
        const out = Array.from(types).map((type, i) => (
          <TaskProperty focus={true} type={type} key={i} />
        ));

        return <div className="flex flex-row gap-2">{out}</div>;
      },
    },
    {
      displayName: "State",
      render: (props: RenderProps) => {
        const statuses = Array.from(new Set(props.statuses));
        if (props.isExpanded && props.summaryRow) {
          return <></>;
        }
        return (
          <div className="flex flex-row gap-2">
            {statuses.map((status, i) => (
              <RunStatus
                status={adjustStatusForDuration(
                  status as RunStatusType,
                  props.taskRuns[i].start_time || undefined,
                  props.taskRuns[i].end_time || undefined,
                  props.currentTime
                )}
                key={i}
              />
            ))}
          </div>
        );
      },
    },
    {
      displayName: "Duration",
      render: (props: RenderProps) => {
        if (props.isExpanded && props.summaryRow) {
          return <></>;
        }
        if (props.taskRuns.length === 1) {
          return (
            <DurationDisplay
              startTime={props.taskRuns[0].start_time || undefined}
              endTime={props.taskRuns[0].end_time || undefined}
              currentTime={new Date()}
            />
          );
        }
        const runTimes = props.taskRuns.map((taskRun) => {
          const startMillis = new Date(
            taskRun.start_time || props.currentTime
          ).getTime();
          const endMillis = new Date(
            taskRun.end_time || props.currentTime
          ).getTime();
          return (endMillis - startMillis) / 1000;
        });
        const meanRunTime =
          runTimes.reduce((a, b) => a + b, 0) / runTimes.length;
        const standardDeviation = Math.sqrt(
          runTimes
            .map((x) => Math.pow(x - meanRunTime, 2))
            .reduce((a, b) => a + b, 0) / runTimes.length
        );
        const timeString =
          runTimes.length > 1
            ? meanRunTime.toFixed(3) +
              " ± " +
              standardDeviation.toFixed(3) +
              "s"
            : meanRunTime.toFixed(3) + "s";
        return <span className="font-semibold">{timeString}</span>;
      },
    },
    {
      displayName: "",
      render: (props: RenderProps) => {
        const anyErrors = props.taskRuns.some(
          (taskRun) => taskRun.status === "FAILURE"
        );
        const tabToLinkTo = anyErrors ? "Errors" : "Output";
        const action = props.runIds.length > 1 ? "diff" : "view";
        const Icon =
          props.runIds.length > 1 ? (
            <TbDelta className="text-lg" />
          ) : (
            <RxMagnifyingGlass className="text-lg" />
          );
        return (
          <Link
            to={`/dashboard/project/${props.projectId}/runs/${props.runIds.join(
              ","
            )}/task/${props.nodeName}?tab=${tabToLinkTo}`}
          >
            <div
              className={`text-white text-sm
            bg-dwlightblue rounded-md px-1 py-1 hover:scale-105 flex flex-row w-16 items-center gap-1 justify-center`}
            >
              <span>{Icon}</span>
              <span>{action}</span>
            </div>
          </Link>
        );
      },
    },
  ];
};

/**
 * TODO -- combine this and the above with the GenericGroupedTable component
 * This has a bit of custom logic but it should be fine now
 * @param props
 * @returns
 */
const GroupedTableRow: React.FC<{
  nodeTemplates: (NodeTemplate | undefined)[];
  codeArtifacts: (CodeArtifact | undefined)[];
  nodeRuns: NodeRunWithAttributes[];
  isSummaryRow: boolean;
  runIds: number[];
  projectVersionIds: number[];
  node: string;
  isHighlighted: boolean;
  projectId: number;
  setHighlighted: (highlighted: boolean) => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  inputNodeValues: any[];
  isOutputNodes: boolean[];
  highlightedRun: number | null;
  setHighlightedRun: (runId: number | null) => void;
  isSubrow: boolean;
  hasAnyTask: boolean;
  currentTime: Date;
}> = (props) => {
  const [expanded, setExpanded] = useState(false);
  const expandable = props.isSummaryRow && props.nodeRuns.length > 1;
  const anyFailed = props.nodeRuns.some(
    (nodeRun) => nodeRun.status === "FAILURE"
  );
  const navigate = useNavigate();
  const runIDs = props.runIds;
  const rows = [
    <tr
      onClick={() => {
        if (expandable) {
          setExpanded(!expanded);
        }
      }}
      // Slight hack as we have summary rows as well as individual rows...
      key={`${props.node}-${runIDs[0]}-${runIDs.length}`}
      id={`#${props.node}`}
      className={`${expandable ? "cursor-cell" : "cursor-default"} ${
        anyFailed && !props.isHighlighted
          ? "bg-dwred/20"
          : anyFailed && props.isHighlighted
          ? "bg-dwred/30"
          : props.isHighlighted
          ? "bg-slate-100"
          : ""
      } h-12`}
      onMouseEnter={() => props.setHighlighted(true)}
      onMouseLeave={() => props.setHighlighted(false)}
    >
      <td></td>
      {cols(props.hasAnyTask).map((col, index) => {
        const ToRender = col.render;
        return (
          <td
            key={index}
            className="py-2 text-sm max-w-sm text-gray-500 whitespace-pre-wrap truncate"
          >
            {
              <ToRender
                toggleExpanded={
                  expandable ? () => setExpanded(!expanded) : undefined
                }
                code={props.codeArtifacts}
                projectId={props.projectId}
                runIds={props.runIds}
                taskRuns={props.nodeRuns}
                statuses={props.nodeRuns.map((nodeRun) => nodeRun.status)}
                nodeName={props.node}
                summaryRow={props.isSummaryRow && props.nodeRuns.length > 1}
                isExpanded={expanded}
                projectVersionIds={props.projectVersionIds}
                navigate={navigate}
                inputNodeValues={props.inputNodeValues}
                isOutputNodes={props.isOutputNodes}
                highlightedRun={props.highlightedRun}
                setHighlightedRun={props.setHighlightedRun}
                isSubrow={props.isSubrow}
                nodeTemplates={props.nodeTemplates}
                currentTime={props.currentTime}
              />
            }
          </td>
        );
      })}
    </tr>,
  ];
  if (expanded) {
    props.nodeRuns.forEach((nodeRun, i) => {
      rows.push(
        <GroupedTableRow
          projectVersionIds={[props.projectVersionIds[i]]}
          nodeRuns={[nodeRun]}
          runIds={[props.runIds[i]]}
          node={props.node}
          isHighlighted={props.isHighlighted}
          projectId={props.projectId}
          setHighlighted={props.setHighlighted}
          isSummaryRow={false}
          inputNodeValues={[props.inputNodeValues[i]]}
          isOutputNodes={[props.isOutputNodes[i]]}
          highlightedRun={props.highlightedRun}
          setHighlightedRun={props.setHighlightedRun}
          isSubrow={true}
          nodeTemplates={[props.nodeTemplates[i]]}
          codeArtifacts={[props.codeArtifacts[i]]}
          hasAnyTask={props.hasAnyTask}
          currentTime={props.currentTime}
        />
      );
    });
  }
  return <>{rows}</>;
};

export const TaskTable: FC<{
  runs: DAGRunWithData[];
  projectVersions: DAGTemplateWithData[];
  highlightedTasks: string[] | null;
  setHighlightedTasks: (tasks: string[] | null) => void;
  isMinimized: boolean;
  setIsMinimized: (minimized: boolean) => void;
  highlightedRun: number | null;
  setHighlightedRun: (runs: number | null) => void;
  projectId: number;
}> = (props) => {
  // TODO -- utilize the project version from the runs, not from the project globals
  // That might be the wrong one, especially now that we're comparing runs
  // const { projectId } = useProjectGlobals();
  // if (projectVersionData === undefined) {
  //   return <Loading />;
  // }

  // const logicalDAG = createLogicalDAG(projectVersionData.dag);
  // This is a hack due to the way we use nodes/map to functions
  // As multiple functions can create the same node, we need to resolve it somehow
  // We should think this through, but for demo purposes this is fine
  const [currentTime, setCurrentTime] = useState(new Date());
  const [count, setCount] = useState(0);

  useEffect(() => {
    setTimeout(() => {
      setCurrentTime(new Date());
      setCount(count + 1);
    }, 1000);
  }, [count]);
  const Icon = props.isMinimized ? HiChevronDown : HiChevronUp;
  const nodeRunMapsByDAGTemplate = new Map<
    number,
    Map<string, NodeRunWithAttributes>
  >();
  props.runs.forEach((run, i) => {
    const nodeMap = new Map<string, NodeRunWithAttributes>();
    run.node_runs.forEach((node) => {
      nodeMap.set(node.node_name, node);
    });
    nodeRunMapsByDAGTemplate.set(
      props.projectVersions[i].id as number,
      nodeMap
    );
  });

  const nodeTemplatesByDAGTemplateId = new Map<
    number,
    Map<string, NodeTemplate>
  >();
  props.projectVersions.forEach((projectVersion, i) => {
    const nodeMap = new Map<string, NodeTemplate>();
    projectVersion.nodes.forEach((node) => {
      nodeMap.set(node.name, node);
    });
    nodeTemplatesByDAGTemplateId.set(
      props.projectVersions[i].id as number,
      nodeMap
    );
  });

  const projectVersionIdsByRunId = new Map<number, number>();
  props.runs.forEach((run, i) => {
    if (props.projectVersions[i].id !== undefined) {
      projectVersionIdsByRunId.set(
        run.id as number,
        props.projectVersions[i].id as number
      );
    }
  });
  // task run, run ID, project version ID
  const tasksGroupedByNodeName = new Map<
    string,
    {
      task: NodeRunWithAttributes;
      runId: number;
      projectVersionId: number;
      codeArtifact: CodeArtifact | undefined;
      nodeTemplate: NodeTemplate | undefined;
    }[]
  >();

  props.runs.forEach((run, i) => {
    // We just zip them together
    const projectVersion = props.projectVersions[i];
    const projectVersionId = projectVersion.id as number;
    const codeArtifactsByID = new Map<number, CodeArtifact>();
    projectVersion.code_artifacts.forEach((codeArtifact) => {
      if (codeArtifact.id === undefined || codeArtifact.id === null) {
        return;
      }
      codeArtifactsByID.set(codeArtifact.id, codeArtifact);
    });
    const nodeTemplatesByTemplateName = new Map<string, NodeTemplate>();
    projectVersion.nodes.forEach((nodeTemplate) => {
      nodeTemplatesByTemplateName.set(nodeTemplate.name, nodeTemplate);
    });

    props.runs[i].node_runs.forEach((task) => {
      if (!tasksGroupedByNodeName.has(task.node_name)) {
        tasksGroupedByNodeName.set(task.node_name, []);
      }
      const nodeTemplate =
        nodeTemplatesByTemplateName.get(task.node_template_name) || undefined;
      // TODO -- handle multiple code artifacts
      const codeArtifactId = nodeTemplate?.code_artifacts?.[0];
      const codeArtifact = codeArtifactId
        ? codeArtifactsByID.get(codeArtifactId)
        : undefined;

      tasksGroupedByNodeName.get(task.node_name)?.push({
        task: task,
        runId: run.id as number,
        projectVersionId: projectVersionId,
        codeArtifact: codeArtifact,
        nodeTemplate: nodeTemplate,
      });
    });
  });
  const runsById = new Map<number, DAGRunWithData>();
  props.runs.forEach((run) => {
    runsById.set(run.id as number, run);
  });

  const taskRowData = Array.from(tasksGroupedByNodeName.entries()).map(
    ([nodeName, tasks]) => {
      return {
        node: nodeName,
        tasks: tasks.map((task) => task.task),
        runIds: tasks.map((task) => task.runId),
        projectVersionIds: tasks.map((task) => task.projectVersionId),
        isOutputNodes: tasks.map(
          (task) =>
            runsById.get(task.runId)?.outputs.indexOf(task.task.node_name) !==
            -1
        ),
        // input nodes have values as well
        inputNodeValues: tasks.map(
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          (task) => (runsById.get(task.runId)?.inputs as any)[nodeName]
        ),
        codeArtifacts: tasks.map((task) => task.codeArtifact),
        nodeTemplates: tasks.map((task) => task.nodeTemplate),
      };
    }
  );
  const hasAnyGroupingTask = props.runs[0].node_runs.some((nodeRun) => {
    const taskName = parseNode(
      nodeRun.node_template_name,
      nodeRun.node_name
    )[0];
    return taskName !== undefined;
  });

  return (
    <div className="">
      <div className="mt-3 flex flex-col">
        <div className="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
            <table className="min-w-full divide-y divide-gray-300">
              <thead>
                <tr className="">
                  <th className="">
                    <div
                      className={`${
                        props.isMinimized
                          ? " justify-start ml-2.5"
                          : " justify-end"
                      } flex  align-middle items-center`}
                    >
                      <Icon
                        className="hover:scale-125 hover:cursor-pointer text-2xl text-gray-400 mr-1"
                        onClick={() => props.setIsMinimized(!props.isMinimized)}
                      />
                    </div>
                  </th>
                  {cols(hasAnyGroupingTask).map((col, index) => (
                    <th
                      key={index}
                      scope="col"
                      className="py-3.5 pr-3 text-left text-sm font-semibold text-gray-900"
                    >
                      {col.displayName}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {!props.isMinimized ? (
                  taskRowData.map(
                    (
                      {
                        node,
                        tasks,
                        runIds,
                        projectVersionIds,
                        inputNodeValues,
                        isOutputNodes,
                        codeArtifacts,
                        nodeTemplates,
                      },
                      index
                    ) => {
                      return (
                        <VisibilitySensor
                          key={index}
                          offset={{ top: -1000, bottom: -1000 }}
                          partialVisibility={true}
                        >
                          {({ isVisible }: { isVisible: boolean }) =>
                            isVisible ? (
                              <GroupedTableRow
                                // TODO -- use the project version we fetched, pass in a list of functions
                                codeArtifacts={codeArtifacts}
                                nodeRuns={tasks}
                                // runId={props.run.id as number}
                                key={index}
                                isHighlighted={
                                  props.highlightedTasks !== null &&
                                  props.highlightedTasks?.indexOf(node) !== -1
                                }
                                setHighlighted={(highlighted) => {
                                  props.setHighlightedTasks(
                                    highlighted ? [node] : null
                                  );
                                }}
                                nodeTemplates={nodeTemplates}
                                projectId={props.projectId as number}
                                runIds={runIds}
                                isSummaryRow={true}
                                projectVersionIds={
                                  projectVersionIds as number[]
                                }
                                inputNodeValues={inputNodeValues}
                                isOutputNodes={isOutputNodes}
                                highlightedRun={props.highlightedRun}
                                setHighlightedRun={props.setHighlightedRun}
                                isSubrow={false}
                                node={node}
                                hasAnyTask={hasAnyGroupingTask}
                                currentTime={currentTime}
                              />
                            ) : (
                              <tr
                                className="h-[50px] bg-gray-100"
                                key={`${node}-${runIds[0]}-${runIds.length}`}
                                id={`#${node}`}
                              ></tr> // Placeholder for invisible rows
                            )
                          }
                        </VisibilitySensor>
                      );
                    }
                  )
                ) : (
                  <div className="divide-y w-full divide-gray-200"></div>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
