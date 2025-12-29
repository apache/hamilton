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

import { Link, createSearchParams, useSearchParams } from "react-router-dom";

import { classNames, getPythonTypeIcon } from "../../../../utils";
import { ErrorView } from "./ErrorView";
import { CodeSummaryView } from "./CodeView";
import { BiChevronLeft } from "react-icons/bi";
import { Fragment } from "react";
import { Menu, MenuItem, MenuItems, Transition } from "@headlessui/react";
import { ChevronDownIcon } from "@heroicons/react/20/solid";
import ReactSelect from "react-select";
import {
  DAGRunWithData,
  DAGTemplateWithData,
  NodeRunWithAttributes,
  NodeTemplate,
  getNodeOutputType,
} from "../../../../state/api/friendlyApi";
import { NodeMetadataPythonType1 } from "../../../../state/api/backendApiRaw";
import { MultiResultSummaryView } from "./result-summaries/DataObservability";
import { RunLink } from "../../../common/CommonLinks";
import { extractCodeContents } from "../../../../utils/codeExtraction";

const tabs = [
  // { name: "Code", href: "#" },
  { name: "Output", href: "#" },
  { name: "Errors", href: "#" },
  { name: "Code", href: "#" },
];
// const ErrorsDisplay = () => {

// }

export const getCodeFromDAGTemplate = (
  templateName: string,
  dagTemplate: DAGTemplateWithData
) => {
  const nodeTemplate = dagTemplate.nodes.find(
    (node) => node.name === templateName
  );
  if (nodeTemplate === undefined) {
    return undefined;
  }
  const codeArtifactId = nodeTemplate.code_artifacts[0];
  if (codeArtifactId === undefined) {
    return undefined;
  }
  const codeArtifact = dagTemplate.code_artifacts.find(
    (codeArtifact) => codeArtifact.id === codeArtifactId
  );
  if (codeArtifact === undefined) {
    return undefined;
  }
  return extractCodeContents(codeArtifact, dagTemplate) || "";
};

type NodeLink = {
  name: string;
  nodeTemplate: NodeTemplate;
  runIds: number[];
  hasData: boolean; // For now we'll grey out the ones we don't have
  // data for but with inputs/whatnot we'll try to get data for everything
};

const computeUpstreamDownstreamNodes = (
  tasks: (NodeRunWithAttributes | null)[],
  projectVersions: DAGTemplateWithData[],
  runs: DAGRunWithData[]
): [NodeLink[], NodeLink[]] => {
  const upstreamNodes = new Map<string, NodeLink>();
  const downstreamNodes = new Map<string, NodeLink>();
  tasks.forEach((task) => {
    // If the task is not included, then we bail
    if (task === null) {
      return;
    }
    const runId = task.dag_run;
    // Then lets get the corresponding run
    const run = runs.find((run) => run.id === runId);
    // Then lets get the corresponding project version
    const projectVersion = projectVersions.find(
      (projectVersion) => projectVersion.id === run?.dag_template
    );
    // Then let's get all the dependencies, we'll map them to types later
    const upstreamDependencies = (task.realized_dependencies || []) as string[];
    // Then let's get all the dowstream dependencies
    const downstreamDependencies =
      run?.node_runs.flatMap((nodeRun) => {
        if (nodeRun.realized_dependencies?.indexOf(task.node_name) !== -1) {
          return [nodeRun.node_name];
        }
        return [];
      }) || [];
    // Then let's gett the mapping of node name -> node template name for that run

    const nodeTemplatesByTemplateName = new Map<string, NodeTemplate>();
    projectVersion?.nodes.forEach((node) => {
      nodeTemplatesByTemplateName.set(node.name, node);
    });

    const nodeRunsByName = (run?.node_runs || []).reduce((acc, nodeRun) => {
      acc.set(nodeRun.node_name, nodeRun);
      return acc;
    }, new Map<string, NodeRunWithAttributes>());
    upstreamDependencies.forEach((dependency) => {
      if (upstreamNodes.has(dependency)) {
        const nodeLink = upstreamNodes.get(dependency) as NodeLink;
        nodeLink.runIds.push(runId as number);
      } else {
        const nodeTemplate = nodeTemplatesByTemplateName.get(
          nodeRunsByName.get(dependency)?.node_template_name || ""
        );
        if (nodeTemplate === undefined) {
          return;
        }
        upstreamNodes.set(dependency, {
          name: dependency,
          nodeTemplate: nodeTemplate,
          runIds: [runId as number],
          hasData: nodeRunsByName.has(dependency),
        });
      }
    });
    downstreamDependencies.forEach((dependency) => {
      if (downstreamNodes.has(dependency)) {
        const nodeLink = downstreamNodes.get(dependency) as NodeLink;
        nodeLink.runIds.push(runId as number);
      } else {
        const nodeTemplate = nodeTemplatesByTemplateName.get(
          nodeRunsByName.get(dependency)?.node_template_name || ""
        );
        if (nodeTemplate === undefined) {
          return;
        }
        downstreamNodes.set(dependency, {
          name: dependency,
          nodeTemplate: nodeTemplate,
          runIds: [runId as number],
          hasData: nodeRunsByName.has(dependency),
        });
      }
    });
  });
  return [
    Array.from(upstreamNodes.values()),
    Array.from(downstreamNodes.values()),
  ];
};

export const SelectRunsToCompare = (props: {
  allRunIds: number[];
  selectedRunIds: number[];
  setRuns: (runIds: number[]) => void;
}) => {
  return (
    <ReactSelect
      onChange={(selected) => {
        if (selected.length == 0) {
          return;
        }
        props.setRuns(selected.map((item) => item.value as number));
      }}
      defaultValue={props.selectedRunIds.map((item) => {
        return { label: item, value: item };
      })}
      placeholder={"Name..."}
      isMulti
      options={Array.from(props.allRunIds).map((name) => {
        return { label: name, value: name };
      })}
    />
  );
};

export const NodeLinkMenu = (props: {
  name: string;
  nodeLinks: NodeLink[];
  projectId: number;
}) => {
  const disabled = props.nodeLinks.length === 0;
  return (
    <Menu as="div" className="relative inline-block text-left">
      <div>
        <Menu.Button
          disabled={disabled}
          className={`inline-flex w-full justify-center gap-x-1.5 rounded-md bg-white px-3
            py-2 text-sm font-semibold shadow-sm ring-1 ring-inset ring-gray-200  ${
              disabled
                ? "text-gray-300"
                : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
            }`}
        >
          {props.name}
          <ChevronDownIcon
            className="-mr-1 h-5 w-5 text-gray-400"
            aria-hidden="true"
          />
        </Menu.Button>
      </div>

      <Transition
        as={Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <MenuItems
          className="absolute right-0 z-10 mt-2
         origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none w-max"
        >
          <div className="py-1">
            {props.nodeLinks.map((nodeLink, i) => {
              const disabled = !nodeLink.hasData;
              const pythonType = getNodeOutputType<NodeMetadataPythonType1>(
                nodeLink.nodeTemplate,
                "NodeMetadataPythonType1"
              );
              const Icon = getPythonTypeIcon(pythonType);
              const multipleRuns = nodeLink.runIds.length > 1;
              return (
                <MenuItem key={i} disabled={disabled}>
                  {() => (
                    <Link
                      to={
                        nodeLink.hasData
                          ? `/dashboard/project/${
                              props.projectId
                            }/runs/${nodeLink.runIds.join(",")}/task/${
                              nodeLink.name
                            }`
                          : "#"
                      }
                      className={classNames(
                        disabled ? "opacity-50" : "",
                        "text-gray-700 hover:bg-gray-100 hover:text-gray-900",
                        "block px-4 py-2 text-sm w-full min-w-max"
                      )}
                    >
                      <div
                        className={`flex flex-row gap-2 ${
                          multipleRuns ? "justify-between" : ""
                        }`}
                      >
                        <div className="flex flex-row items-center gap-1">
                          <Icon></Icon>
                          <p>{nodeLink.name}</p>
                        </div>
                        <div className="flex flex-row items-center gap-1">
                          {nodeLink.runIds.map((runId) => (
                            <RunLink
                              key={runId}
                              projectId={props.projectId}
                              runId={runId}
                              setHighlightedRun={() => void 0}
                              highlightedRun={null}
                            ></RunLink>
                          ))}
                        </div>
                      </div>
                    </Link>
                  )}
                </MenuItem>
              );
            })}
          </div>
        </MenuItems>
      </Transition>
    </Menu>
  );
};
// const NodeLinkSection = (props: {
//   upstreamNodes: NodeLink[];
//   downstreamNodes: NodeLink[];
// }) => {
//   return (
//     <div className="p-2">
//       <div className=" w-min flex flex-row gap-2">
//         {props.upstreamNodes.map((nodeLink, i) => {
//           return <NodeLinkView nodeLink={nodeLink} key={i} />;
//         })}
//       </div>
//       <div className="w-min flex flex-row gap-2">
//         {props.downstreamNodes.map((nodeLink, i) => {
//           return <NodeLinkView nodeLink={nodeLink} key={i} />;
//         })}
//       </div>
//     </div>
//   );
// };
export const TaskView = (props: {
  projectVersions: DAGTemplateWithData[];
  taskName: string;
  projectId: number;
  knownRunIds: number[];
  setRuns: (runs: number[]) => void;
  nodeRunData: (NodeRunWithAttributes | null)[];
  fullRuns: DAGRunWithData[];
}) => {
  const { nodeRunData, projectVersions, taskName, fullRuns } = props;
  const correspondingCode = projectVersions.map((projectVersion, i) => {
    //TODO -- figure out if this can be/why this would be undefined
    const templateName = nodeRunData[i]?.node_template_name || taskName;
    const out = getCodeFromDAGTemplate(templateName, projectVersion);
    return out || "";
  });

  const [upstreamNodes, downstreamNodes] = computeUpstreamDownstreamNodes(
    props.nodeRunData,
    projectVersions,
    fullRuns
  );
  const [searchParams, setSearchParams] = useSearchParams(
    createSearchParams({ tab: "Output" })
  );
  const path = window.location.pathname;
  const setWhichTab = (tab: string) => {
    setSearchParams(createSearchParams({ tab: tab }));
  };
  const whichTab = searchParams.get("tab");
  return (
    <div className="pt-10 flex flex-col gap-5">
      <div className="sm:hidden">
        <label htmlFor="tabs" className="sr-only">
          Select a tab
        </label>
        <select
          id="tabs"
          name="tabs"
          className="block w-full rounded-md border-gray-300 focus:border-dwdarkblue focus:bg-dwdarkblue/10"
          defaultValue={"Output"}
        >
          {tabs.map((tab) => (
            <option
              onClick={() => {
                setWhichTab(tab.name);
              }}
              key={tab.name}
            >
              {tab.name}
            </option>
          ))}
        </select>
      </div>
      <div className="hidden sm:block">
        <nav className="flex space-x-4 items-center" aria-label="Tabs">
          <Link
            className={classNames(
              "text-gray-500 hover:text-gray-700",
              "py-2 font-medium text-md rounded-md"
            )}
            to={path.split("/task/")[0]}
          >
            <BiChevronLeft className="inline-block text-2xl" />
          </Link>
          {tabs.map((tab) => (
            <a
              onClick={() => {
                setWhichTab(tab.name);
              }}
              key={tab.name}
              href={tab.href}
              className={classNames(
                tab.name == whichTab
                  ? "bg-dwdarkblue/20 text-dwdarkblue"
                  : "text-gray-500 hover:text-gray-700",
                "px-3 py-2 font-medium text-md rounded-md"
              )}
              aria-current={tab.name == whichTab ? "page" : undefined}
            >
              {tab.name}
            </a>
          ))}
          <NodeLinkMenu
            name="Upstream"
            nodeLinks={upstreamNodes}
            projectId={props.projectId}
          />
          <NodeLinkMenu
            name="Downstream"
            nodeLinks={downstreamNodes}
            projectId={props.projectId}
          />
          <SelectRunsToCompare
            allRunIds={props.knownRunIds}
            selectedRunIds={
              props.nodeRunData
                .map((i) => i?.dag_run)
                .filter((i) => i !== undefined) as number[]
            }
            setRuns={props.setRuns}
          ></SelectRunsToCompare>
        </nav>
      </div>
      {/* <NodeLinkSection
        upstreamNodes={upstreamNodes}
        downstreamNodes={downstreamNodes}
      /> */}
      <h2 className="text-gray-800 text-xl pb-2 font-semibold">{taskName}</h2>

      {whichTab === "Errors" ? (
        <div className="pt-4">
          <ErrorView
            codes={correspondingCode}
            nodeRunData={nodeRunData}
          ></ErrorView>
        </div>
      ) : whichTab === "Output" ? (
        <MultiResultSummaryView
          projectId={props.projectId}
          nodeRunData={nodeRunData}
          taskName={taskName}
          runIds={fullRuns.map((i) => i.id as number)}
        />
      ) : whichTab === "Code" ? (
        <CodeSummaryView nodeRunData={nodeRunData} codes={correspondingCode} />
      ) : (
        <></>
      )}
    </div>
  );
};
