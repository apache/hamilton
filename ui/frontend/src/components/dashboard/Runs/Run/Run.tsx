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

import { useEffect, useState } from "react";
import { Outlet, useLocation, useOutletContext } from "react-router-dom";
import {
  useDAGRunsByIds,
  useDAGTemplatesByID,
} from "../../../../state/api/friendlyApi";
import {
  DAGTemplateWithData,
  DAGRunWithData,
} from "../../../../state/api/friendlyApi";
import { Loading } from "../../../common/Loading";
import { TaskTable } from "./TaskTable";
import WaterfallChart from "./WaterfallChart";
import { Tabs } from "../../../common/GenericTabbedView";
import { DashboardItem, MetricDisplay } from "../Dashboarding";
import { Link } from "react-router-dom";
import { DagRunOutWithData } from "../../../../state/api/backendApiRaw";
import { skipToken } from "@reduxjs/toolkit/dist/query";
import { useURLParams } from "../../../../state/urlState";
import { RunLink } from "../../../common/CommonLinks";
import { DAGRunView } from "./DAGRunView";
import { Switch } from "@headlessui/react";
import { classNames } from "../../../../utils";

const REFRESH_SECONDS = 10;
const TOTAL_DURATION = 1000; //a thousand seconds and we want it to stop refreshing
const RUN_TOO_OLD = 7200; //an hour, we don't want to refresh if its that old...

type ContextType = {
  runs: DAGRunWithData[];
  dagTemplates: DAGTemplateWithData[];
};

export const useRunData = () => {
  return useOutletContext<ContextType>();
};

export const TaskProperty = (props: {
  type: "input" | "output" | "config";
  displayName?: string;
  focus: boolean;
}) => {
  const displayName = props.displayName ?? props.type;
  const color = props.focus ? "bg-yellow-500" : "bg-yellow-500/60";
  return (
    <span className={`${color} text-white text-sm px-1 py-1 rounded-md`}>
      {displayName}
    </span>
  );
};

const RunInfoDisplay = (props: {
  setHighlightedRun: (run: number | null) => void;
  highlightedRun: number | null;
  runs: DAGRunWithData[];
  projectVersions: DAGTemplateWithData[];
  projectId: number;
}) => {
  return (
    <div
      className={`flex flex-col align-middle items-center text-dwdarkblue gap-3 justify-center h-full p-3`}
    >
      <div className="flex flex-col gap-3 text-sm">
        {props.projectVersions.map((projectVersion, i) => {
          return (
            <div
              className={`cursor-default hover:bg-dwdarkblue/5 rounded-md flex flex-wrap gap-1 items-center p-1 ${
                props.highlightedRun === (props.runs[i].id as number)
                  ? "bg-dwdarkblue/5"
                  : ""
              }`}
              onMouseEnter={() => {
                props.setHighlightedRun(props.runs[i].id as number);
              }}
              onMouseLeave={() => {
                props.setHighlightedRun(null);
              }}
              key={i}
            >
              <RunLink
                setHighlightedRun={props.setHighlightedRun}
                highlightedRun={props.highlightedRun}
                projectId={props.projectId}
                runId={props.runs[i].id as number}
              />
              <Link
                to={`/dashboard/project/${props.projectId}/versions/${props.projectVersions[i].id}`}
                className="text-sm hover:underline font-light text-dwlightblue items-center"
              >
                {projectVersion.name}
              </Link>{" "}
              <span className="text-gray-400">
                ({props.runs[i].username_resolved})
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const VariableTable = (props: {
  variables: Map<string, string[]>;
  runs: DAGRunWithData[];
  projectIds: number[];
  variableType: string;
  setHighlightedRun: (run: number | null) => void;
  highlightedRun: number | null;
}) => {
  return (
    <div className="mt-0 flow-root p-2 max-w-full">
      <div className="-my-2 overflow-x-visible ">
        <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
          <table className="min-w-full divide-y divide-gray-300">
            <thead>
              <tr>
                <th className="pl-4 pr-3 py-2 text-lg text-gray-700 sm:pl-0 text-center font-semibold">
                  {props.variableType}
                </th>
                {props.runs.map((run, i) => (
                  <th
                    key={i}
                    scope="col"
                    className="pl-4 pr-3 py-2 text-sm font-normal text-gray-800 sm:pl-0 text-start"
                  >
                    <RunLink
                      setHighlightedRun={props.setHighlightedRun}
                      highlightedRun={props.highlightedRun}
                      projectId={props.projectIds[i]}
                      runId={run.id as number}
                    />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {Array.from(props.variables.entries()).map(
                ([variableKey, values]) => {
                  const hasDiff = new Set(values).size > 1;
                  return (
                    <tr key={variableKey}>
                      <td
                        key={variableKey + "-header"}
                        className="whitespace-nowrap px-3 py-4 text-sm text-gray-500 font-semibold"
                      >
                        <code>{variableKey}</code>
                      </td>
                      {values.map((value, i) => {
                        let json_string = "";
                        if (value) {
                          json_string = JSON.stringify(value, null, 2);
                          if (json_string.length > 10000) {
                            json_string = json_string.substring(0, 10000) + " (truncated)";
                          }
                        }
                        return (
                          <td
                            onMouseEnter={() => {
                              props.setHighlightedRun(
                                props.runs[i].id as number
                              );
                            }}
                            onMouseLeave={() => {
                              props.setHighlightedRun(null);
                            }}
                            key={i}
                            className={`truncate break-words px-3 py-4 text-sm ${
                              hasDiff
                                ? "bg-yellow-400 text-gray-700"
                                : "text-gray-500"
                            } ${
                              hasDiff &&
                              props.highlightedRun === props.runs[i].id
                                ? "bg-yellow-400/50"
                                : hasDiff
                                ? "bg-yellow-400"
                                : props.highlightedRun === props.runs[i].id
                                ? "bg-dwdarkblue/5"
                                : ""
                            }`}
                          >
                            <div className="max-w-64 max-h-48 overflow-scroll scrollbar-hide">
                              <code className="whitespace-pre-wrap truncate">
                                {json_string}
                              </code>
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  );
                }
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const InputsDisplay = (props: {
  runs: DAGRunWithData[];
  projectVersions: DAGTemplateWithData[];
  setHighlightedRun: (run: number | null) => void;
  highlightedRun: number | null;
  projectId: number;
}) => {
  const variables = new Map<string, string[]>();
  const allRunInputs = new Set<string>();
  props.runs.forEach((run) =>
    Object.entries(run.inputs || {}).forEach((entry) => {
      allRunInputs.add(entry[0]);
    })
  );
  // const allRunInputsArray = Array.from(allRunInputs).sort();
  props.runs.forEach((run) => {
    allRunInputs.forEach((input) => {
      const runInputs = run.inputs as Record<string, string>;
      const value = runInputs?.[input];
      variables.set(input, [...(variables.get(input) ?? []), value]);
    });
  });
  return (
    <VariableTable
      variables={variables}
      runs={props.runs}
      projectIds={props.projectVersions.map(() => props.projectId)}
      variableType="Inputs"
      setHighlightedRun={props.setHighlightedRun}
      highlightedRun={props.highlightedRun}
    />
  );
};

const ConfigDisplay = (props: {
  runs: DAGRunWithData[];
  projectVersions: DAGTemplateWithData[];
  highlightedRun: number | null;
  setHighlightedRun: (run: number | null) => void;
  projectId: number;
}) => {
  const variables = new Map<string, string[]>();
  const allRunConfigs = new Set<string>();
  props.projectVersions.forEach((projectVersion) =>
    Object.entries(projectVersion.config || {}).forEach((entry) => {
      allRunConfigs.add(entry[0]);
    })
  );
  // const allRunInputsArray = Array.from(allRunInputs).sort();
  props.projectVersions.forEach((projectVersion) => {
    allRunConfigs.forEach((config) => {
      const runInputs = projectVersion.config as Record<string, string>;
      const value = runInputs[config];
      variables.set(config, [...(variables.get(config) ?? []), value]);
    });
  });
  return (
    <VariableTable
      highlightedRun={props.highlightedRun}
      setHighlightedRun={props.setHighlightedRun}
      variables={variables}
      runs={props.runs}
      projectIds={props.projectVersions.map(() => props.projectId)}
      variableType="Config"
    />
  );
};

const TagDisplay = (props: {
  runs: DAGRunWithData[];
  projectVersions: DAGTemplateWithData[];
  highlightedRun: number | null;
  setHighlightedRun: (run: number | null) => void;
  projectId: number;
}) => {
  const variables = new Map<string, string[]>();
  const allTags = new Set<string>();
  props.runs.forEach((run) =>
    Object.entries(run.tags || {}).forEach((entry) => {
      allTags.add(entry[0]);
    })
  );
  // const allRunInputsArray = Array.from(allRunInputs).sort();
  props.runs.forEach((run) => {
    allTags.forEach((tag) => {
      const runTags = run.tags as Record<string, string>;
      const value = runTags[tag];
      variables.set(tag, [...(variables.get(tag) ?? []), value]);
    });
  });
  return (
    <VariableTable
      highlightedRun={props.highlightedRun}
      setHighlightedRun={props.setHighlightedRun}
      variables={variables}
      runs={props.runs}
      projectIds={props.projectVersions.map(() => props.projectId)}
      variableType="Tags"
    />
  );
};

// const ConfigDisplay = (props: { runs: RunLogOutWithRun[] }) => {
//   return (
//     <div
//       className={`flex flex-col align-middle items-center text-dwdarkblue gap-3 justify-center h-full`}
//     >
//       <div className={`text-2xl font-semibold`}>Config</div>
//       <div className="flex flex-col gap-1"></div>
//     </div>
//   );
// };

const OutputsDisplay = (props: {
  runs: DAGRunWithData[];
  projectVersions: DAGTemplateWithData[];
  highlightedRun: number | null;
  setHighlightedRun: (runId: number | null) => void;
  setHighlightedTasks: (task: string[] | null) => void;
  highlightedTasks: string[] | null;
}) => {
  const allOutputs = new Set<string>();
  const outputsByRun = new Map<number, Set<string>>();
  props.runs.forEach((run) => {
    const outputs = (run.outputs || []) as string[];
    outputs.forEach((output) => {
      allOutputs.add(output);
    });
    outputsByRun.set(run.id as number, new Set(outputs));
  });
  return (
    <div
      className={`flex flex-wrap align-middle items-center text-dwdarkblue gap-3 justify-center h-full p-3 w-full`}
    >
      <div className={`text-2xl font-semibold text-dwdarkblue`}>Outputs</div>
      <div className="flex flex-row items-center gap-2 text-sm">
        {props.runs.flatMap((item, i) => {
          const numOutputs = outputsByRun.get(item.id as number)?.size ?? 0;
          return [
            <RunLink
              key={i}
              projectId={props.projectVersions[i].id as number}
              runId={item.id as number}
              setHighlightedRun={props.setHighlightedRun}
              highlightedRun={props.highlightedRun}
            />,
            <div
              key={i + "_numOutputs"}
              className={`${
                props.highlightedRun === item.id
                  ? "text-gray-600"
                  : "text-gray-400"
              } `}
            >
              {`(${numOutputs})`}
            </div>,
          ];
        })}
      </div>
      <div className="flex flex-wrap gap-1 ">
        {Array.from(allOutputs)
          .sort()
          .map((outputName, i) => (
            <div
              key={i}
              onMouseEnter={() => {
                props.setHighlightedTasks([outputName]);
              }}
              onMouseLeave={() => {
                props.setHighlightedTasks(null);
              }}
              className="cursor-pointer"
              onClick={() => {
                const node = document.getElementById(`#${outputName}`);
                node?.scrollIntoView({ behavior: "smooth", block: "center" });
              }}
            >
              <TaskProperty
                type="input"
                key={i}
                displayName={outputName}
                focus={
                  (props.highlightedTasks?.indexOf(outputName) || -1) > -1 ||
                  (props.highlightedRun &&
                    outputsByRun.get(props.highlightedRun)?.has(outputName)) ||
                  false
                }
              />
            </div>
          ))}
      </div>
    </div>
  );
};

const NumTasksDisplay = (props: {
  runs: DAGRunWithData[];
  setHighlightedRun: (runId: number | null) => void;
  highlightedRun: number | null;
  projectVersions: DAGTemplateWithData[];
  projectId: number;
}) => {
  return (
    <div className="flex flex-col justify-center items-center h-full w-full py-5 text-dwdarkblue/80 gap-2">
      {/* <h1 className="text-2xl font-semibold">Nodes</h1> */}
      <div className="flex flex-row gap-10 justify-between">
        {props.runs.map((run) => (
          <div
            className={`${
              run.id === props.highlightedRun
                ? "bg-dwdarkblue/5 rounded-md"
                : ""
            } cursor-default p-2`}
            key={run.id}
            onMouseEnter={() => props.setHighlightedRun(run.id as number)}
            onMouseLeave={() => props.setHighlightedRun(null)}
          >
            <MetricDisplay
              number={run.node_runs.length}
              textColorClass={""}
              isSubset={false}
              label={
                <span className="text-sm">
                  <span>nodes </span>
                  <RunLink
                    projectId={props.projectId}
                    runId={run.id as number}
                    setHighlightedRun={props.setHighlightedRun}
                    highlightedRun={props.highlightedRun}
                  />
                </span>
              }
            />
          </div>
        ))}
      </div>
    </div>
  );
};
const getRuntime = (run: DagRunOutWithData) => {
  const start = new Date(run.run_start_time || Date.now());
  const end = run.run_end_time
    ? new Date(run.run_end_time)
    : new Date(Date.now());
  return (end.getTime() - start.getTime()) / 1000;
};

const RuntimeDurationDisplay = (props: {
  runs: DAGRunWithData[];
  highlightedRun: number | null;
  setHighlightedRun: (runId: number | null) => void;
  projectVersions: DAGTemplateWithData[];
  projectId: number;
}) => {
  const [times, setTimes] = useState(props.runs.map(getRuntime));
  const [count, setCount] = useState(0);
  useEffect(() => {
    setTimes(props.runs.map(getRuntime));
    setTimeout(() => setCount((count) => count + 1), 1000);
  }, [count, props.runs]);

  return (
    <div className="flex flex-col justify-center items-center h-full w-full py-5 text-dwdarkblue/80 gap-2">
      <div className="flex flex-row gap-10 justify-between">
        {props.runs.map((run, i) => (
          <div
            className={`${
              run.id === props.highlightedRun
                ? "bg-dwdarkblue/5 rounded-md"
                : ""
            } cursor-default p-2`}
            key={run.id}
            onMouseEnter={() => props.setHighlightedRun(run.id as number)}
            onMouseLeave={() => props.setHighlightedRun(null)}
          >
            <MetricDisplay
              key={run.id}
              number={times[i]}
              label={
                <span className="text-sm">
                  <span>seconds </span>
                  <RunLink
                    projectId={props.projectId}
                    runId={run.id as number}
                    setHighlightedRun={props.setHighlightedRun}
                    highlightedRun={props.highlightedRun}
                  />
                </span>
              }
              textColorClass={"text-dwdarkblue"}
              isSubset={false}
              numberFormatter={(num) => `${num.toFixed(2)}`}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

const ParametersDashboard = (props: {
  displayInputData?: boolean;
  displayConfigData?: boolean;
  displayOutputData?: boolean;
  displayTagData?: boolean;
  runs: DAGRunWithData[];
  projectVersions: DAGTemplateWithData[];
  highlightedRun: number | null;
  setHighlightedRun: (runId: number | null) => void;
  setHighlightedTasks: (task: string[] | null) => void;
  highlightedTasks: string[] | null;
  projectId: number;
}) => {
  const {
    displayInputData,
    displayConfigData,
    runs,
    projectVersions,
    highlightedRun,
    setHighlightedRun,
    projectId,
  } = props;

  return (
    <div className="flex flex-wrap">
      {displayInputData && (
        <DashboardItem>
          <InputsDisplay
            highlightedRun={highlightedRun}
            setHighlightedRun={setHighlightedRun}
            runs={runs as DAGRunWithData[]}
            projectVersions={projectVersions as DAGTemplateWithData[]}
            projectId={projectId as number}
          />
        </DashboardItem>
      )}

      {displayConfigData && (
        <DashboardItem>
          <ConfigDisplay
            highlightedRun={highlightedRun}
            setHighlightedRun={setHighlightedRun}
            runs={runs}
            projectVersions={projectVersions}
            projectId={projectId as number}
          />
        </DashboardItem>
      )}
    </div>
  );
};

const InfoDashboard = (props: {
  runs: DAGRunWithData[];
  projectVersions: DAGTemplateWithData[];
  highlightedRun: number | null;
  setHighlightedRun: (runId: number | null) => void;
  projectId: number;
  displayTagData: boolean;
  displayOutputData: boolean;
  setHighlightedTasks: (task: string[] | null) => void;
  highlightedTasks: string[] | null;
}) => {
  const {
    runs,
    projectVersions,
    highlightedRun,
    setHighlightedRun,
    projectId,
    displayTagData,
    displayOutputData,
    setHighlightedTasks,
    highlightedTasks,
  } = props;
  return (
    <div className="flex flex-wrap">
      <DashboardItem>
        <RunInfoDisplay
          highlightedRun={highlightedRun}
          setHighlightedRun={setHighlightedRun}
          runs={runs}
          projectVersions={projectVersions}
          projectId={projectId as number}
        />
      </DashboardItem>
      <DashboardItem>
        <NumTasksDisplay
          projectVersions={projectVersions}
          runs={runs}
          setHighlightedRun={setHighlightedRun}
          highlightedRun={highlightedRun}
          projectId={projectId as number}
        />
      </DashboardItem>
      <DashboardItem>
        <RuntimeDurationDisplay
          projectVersions={projectVersions}
          runs={runs}
          highlightedRun={highlightedRun}
          setHighlightedRun={setHighlightedRun}
          projectId={projectId as number}
        />
      </DashboardItem>
      {displayTagData && (
        <DashboardItem>
          <TagDisplay
            highlightedRun={highlightedRun}
            setHighlightedRun={setHighlightedRun}
            runs={runs}
            projectVersions={projectVersions}
            projectId={projectId as number}
          />
        </DashboardItem>
      )}
      {displayOutputData && (
        <DashboardItem>
          <OutputsDisplay
            setHighlightedTasks={setHighlightedTasks}
            highlightedTasks={highlightedTasks}
            runs={runs}
            highlightedRun={highlightedRun}
            setHighlightedRun={setHighlightedRun}
            projectVersions={projectVersions}
          />
        </DashboardItem>
      )}
    </div>
  );
};

const AutoRefreshButton = (props: {
  refetch: () => void;
  shouldRefreshByDefault: boolean;
}) => {
  const [enabled, setEnabled] = useState(props.shouldRefreshByDefault);
  const [elapsedTime, setElapsedTime] = useState(0);
  const { refetch } = props;

  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;

    if (enabled && elapsedTime < TOTAL_DURATION) {
      // Set interval only if enabled and total duration not reached
      intervalId = setInterval(() => {
        refetch(); // Call the refetch function
        setElapsedTime((prevTime) => prevTime + REFRESH_SECONDS); // Update elapsed time
      }, REFRESH_SECONDS * 1000); // Convert seconds to milliseconds
    } else {
      // Disable auto-refresh and reset elapsed time if total duration is reached
      setEnabled(false);
      setElapsedTime(0);
    }

    // Clear interval on component unmount or when disabled
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [enabled, elapsedTime, refetch]);

  return (
    <Switch.Group as="div" className="flex items-center pl-10">
      <Switch
        checked={enabled}
        onChange={setEnabled}
        className={classNames(
          enabled ? "bg-dwdarkblue" : "bg-gray-200",
          "relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-dwdarkblue focus:ring-offset-2"
        )}
      >
        <span
          aria-hidden="true"
          className={classNames(
            enabled ? "translate-x-5" : "translate-x-0",
            "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
          )}
        />
      </Switch>
      <Switch.Label as="span" className="ml-3 text-sm">
        <span className="font-medium text-gray-500"> Auto refresh</span>{" "}
        <span className="text-gray-400">(Every {REFRESH_SECONDS} seconds)</span>
      </Switch.Label>
    </Switch.Group>
  );
};

const Run = () => {
  const location = useLocation();
  const [highlightedTasks, setHighlightedTasks] = useState<string[] | null>(
    null
  );
  // TODO -- fix this up. We really should be using contexts all the way down *or* URL params...
  // const run = useRun({ runId: parseInt(location.pathname.split("/")[3]) });
  const { runIds: runIdsRaw, projectId } = useURLParams();
  // const run = useRun({ runId: parseInt(runId as string) });
  const runs = useDAGRunsByIds({ dagRunIds: runIdsRaw?.join(",") || "" });

  // Currently we just assume the project versions are all the same...
  const projectVersionIds =
    runs.data?.map((run) => run.dag_template) || undefined;
  const projectVersions = useDAGTemplatesByID(
    projectVersionIds !== undefined
      ? { dagTemplateIds: projectVersionIds.join(",") || "" }
      : skipToken
  );

  const [highlightedRun, setHighlightedRun] = useState<number | null>(null);
  const [whichView, setWhichView] = useState<string>("waterfall");
  const [dagViewHidden, setDagViewHidden] = useState<boolean>(false);
  const [tableViewHidden, setTableViewHidden] = useState<boolean>(false);
  const [dashboardViewHidden, setDashboardViewHidden] =
    useState<boolean>(false);
  const [whichDashboardView, setWhichDashboardView] = useState<string>("info");

  if (
    runs.isLoading ||
    projectVersions.isLoading ||
    projectVersions.isFetching ||
    projectVersions.isUninitialized
  ) {
    return <Loading />;
  }
  if (runs.data === undefined) {
    return (
      <div>
        Run not found/not parseable. Please reach out to the DAGWorks team...
      </div>
    );
  }
  if (projectVersions.data === undefined) {
    return <div>Project data cannot load...</div>;
  }
  // only display the variable data
  const displayOutputData =
    (runs.data || []).filter((run) => {
      return (run.outputs || []).length > 0;
    }).length > 0;

  const displayInputData =
    (runs.data || []).filter((run) => {
      return Object.entries(run.inputs || {}).length > 0;
    }).length > 0;

  const displayConfigData =
    (projectVersions.data || []).filter((projectVersion) => {
      return Object.entries(projectVersion.config || {}).length > 0;
    }).length > 0;

  const shouldRefreshByDefault =
    runs.data?.some(
      (run) => run.run_status === "RUNNING" && getRuntime(run) < RUN_TOO_OLD
    ) || false;

  const displayTagData =
    (runs.data || []).filter((run) => {
      return Object.entries(run.tags || {}).length > 0;
    }).length > 0;

  // const dags = projectVersions.data.map((projectVersion) => {
  //   return createLogicalDAG(projectVersion.dag);
  // });
  // const dag = createLogicalDAG(projectVersion.data.dag);
  const inOutlet = location.pathname.includes("/task/");
  return inOutlet ? (
    // TODO -- determine the right way to compare the set of runs and pass the data down
    // The best way is to compare a task across runs -- when you click on it it keeps the comma-separated runs list in the URL
    <Outlet
      context={{
        runs: runs.data as DAGRunWithData[],
        dagTemplates: projectVersions.data as DAGTemplateWithData[],
      }}
    />
  ) : (
    <div className="pt-10">
      <Tabs
        isMinimized={dashboardViewHidden}
        setIsMinimized={setDashboardViewHidden}
        allTabs={[
          { name: "info", displayName: "Run Info" },
          { name: "parameters", displayName: "Run Parameters" },
        ]}
        currentTab={whichDashboardView}
        setCurrentTab={setWhichDashboardView}
        additionalElement={
          <AutoRefreshButton
            refetch={runs.refetch}
            shouldRefreshByDefault={shouldRefreshByDefault}
          />
        }
      />
      {!dashboardViewHidden && whichDashboardView === "info" && (
        <InfoDashboard
          runs={runs.data as DAGRunWithData[]}
          projectVersions={projectVersions.data as DAGTemplateWithData[]}
          highlightedRun={highlightedRun}
          setHighlightedRun={setHighlightedRun}
          projectId={projectId as number}
          displayOutputData={displayOutputData}
          displayTagData={displayTagData}
          setHighlightedTasks={setHighlightedTasks}
          highlightedTasks={highlightedTasks}
        />
      )}
      {!dashboardViewHidden && whichDashboardView === "parameters" && (
        <ParametersDashboard
          runs={runs.data as DAGRunWithData[]}
          projectVersions={projectVersions.data as DAGTemplateWithData[]}
          highlightedRun={highlightedRun}
          setHighlightedRun={setHighlightedRun}
          setHighlightedTasks={setHighlightedTasks}
          highlightedTasks={highlightedTasks}
          projectId={projectId as number}
          displayInputData={displayInputData}
          displayConfigData={displayConfigData}
          displayOutputData={displayOutputData}
          displayTagData={displayTagData}
        />
      )}

      <div className="sticky bg-white top-0 z-50">
        <Tabs
          isMinimized={dagViewHidden}
          setIsMinimized={setDagViewHidden}
          allTabs={[
            { name: "dag", displayName: "DAG View" },
            { name: "waterfall", displayName: "Waterfall" },
          ]}
          currentTab={whichView}
          setCurrentTab={setWhichView}
        />
        {!dagViewHidden &&
          (whichView === "dag" ? (
            <div>
              <div className="w-[100%] h-[500px] flex flex-row">
                {(runs.data || []).map((run, i) => (
                  <div
                    key={i}
                    style={{
                      width: `${100 / (runs.data?.length || 0)}%`,
                      height: "100%",
                    }}
                  >
                    <DAGRunView
                      dagTemplate={
                        ((projectVersions.data || []) as DAGTemplateWithData[])[
                          i
                        ]
                      }
                      run={run}
                      highlightedTasks={highlightedTasks}
                      setHighlightedTasks={setHighlightedTasks}
                      isHighlighted={highlightedRun === run.id}
                      setHighlighted={(highlighted: boolean) => {
                        setHighlightedRun(
                          highlighted ? (run.id as number) : null
                        );
                      }}
                    />
                  </div>
                ))}
              </div>
            </div>
          ) : whichView === "waterfall" ? (
            <div className="w-[100%]  flex flex-col sm:flex-row items-center ">
              {runs.data.map((run, i) => (
                <div
                  key={i}
                  style={{ width: `${100 / (runs.data?.length || 0)}%` }}
                >
                  <WaterfallChart
                    key={i}
                    run={run}
                    highlightedTasks={highlightedTasks}
                    setHighlightedTasks={setHighlightedTasks}
                    isHighlighted={highlightedRun === run.id}
                    setHighlighted={(highlighted: boolean) => {
                      setHighlightedRun(
                        highlighted ? (run.id as number) : null
                      );
                    }}
                  />
                </div>
              ))}
            </div>
          ) : (
            <></>
          ))}
      </div>
      <div className="sticky">
        <TaskTable
          isMinimized={tableViewHidden}
          setIsMinimized={setTableViewHidden}
          runs={runs.data as DAGRunWithData[]}
          projectVersions={projectVersions.data as DAGTemplateWithData[]}
          highlightedTasks={highlightedTasks}
          setHighlightedTasks={setHighlightedTasks}
          highlightedRun={highlightedRun}
          setHighlightedRun={setHighlightedRun}
          projectId={projectId as number}
        />
      </div>
    </div>
  );
};

export default Run;
