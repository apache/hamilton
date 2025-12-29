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

import { createContext, useContext } from "react";
import { DAGNode, GroupSpec } from "./types";
import { iconForGroupSpecName, iconsForNodes } from "./utils";
import { getAdapterIcon } from "../../../utils";
import { getColorFromStatus } from "../Runs/Status";
import { RunStatusType } from "../../../state/api/friendlyApi";
import { NodeControlContext, extractArtifactTypes } from "./DAGViz";
import { Handle, Position } from "reactflow";

/**
 * This is a bit hacked together because I ran out of time. Things to do:
 * 1. Get it so we also have grouping
 * 2. Combine it with the other DAGs on the page (basically there, just
 * need to wire up the higher levels that call out to this)
 * 3. Add more execution-spec stuff
 *
 */
export const DAGRunViewContext = createContext({
  highlighedTasks: new Set<string>(),
});

export const ExecutionNodeComponent = (props: {
  data: {
    nodes: DAGNode[];
    displayName: string;
    collapsed: boolean;
    groupSpec: GroupSpec;
  };
  id: string;
}) => {
  const { highlighedTasks } = useContext(DAGRunViewContext);
  const NodeIcons =
    props.data.groupSpec.groupSpecName === "node"
      ? iconsForNodes(props.data.nodes)
      : [iconForGroupSpecName(props.data.groupSpec.groupSpecName)];

  const isInput = props.data.nodes
    .map((item) => item.nodeTemplate.classifications.includes("input"))
    .some((i) => i);
  const hidden = props.data.collapsed;

  const { vertical } = useContext(NodeControlContext);

  // console.log(selectedNodes)
  const nodeRuns = props.data.nodes.flatMap((node) => node.nodeRuns || []);
  const containsFailedNode = nodeRuns.some((n) => n.status === "FAILURE");
  const containsRunningNode = nodeRuns.some((n) => n.status === "RUNNING");
  const containsSucceededNode = nodeRuns.some((n) => n.status === "SUCCESS");

  const isSelected = props.data.nodes
    .map((i) => i.name)
    .some((i) => highlighedTasks.has(i));

  let displayStatus = "NOT_RUN";
  if (containsRunningNode) {
    displayStatus = "RUNNING";
  } else if (containsFailedNode) {
    displayStatus = "FAILURE";
  } else if (containsSucceededNode) {
    displayStatus = "SUCCESS";
  }
  const { background, text } = !isInput
    ? getColorFromStatus(displayStatus as RunStatusType)
    : {
        background: "bg-transparent",
        text: "text-dwdarkblue",
      };

  const artifactTypes = extractArtifactTypes(props.data.nodes);

  const hasArtifact = artifactTypes.size > 0;

  return (
    <div
      className={`group flex flex-col gap-3 items-center cursor-cell bg-opacity-0 ${text} ${
        isSelected ? "opacity-80" : ""
      } ${hasArtifact ? "border border-dashed " : " "} rounded-lg ${background}
      ${isInput ? " border-2 border-dwdarkblue/50 p-0" : " text-white p-1"}`}
    >
      {artifactTypes.size > 0 ? (
        <div className="flex flex-row">
          {Array.from(artifactTypes).map((artifactType, i) => {
            const Icon = getAdapterIcon(artifactType);
            return (
              <Icon
                className={`text-5xl group-hover:text-opacity-80 ${text}`}
                key={i}
              />
            );
          })}
        </div>
      ) : (
        <></>
      )}
      <div
        className={` ${background}  h-max w-max text-sm p-1 rounded-md cursor-cell ${
          hidden ? "hidden" : ""
        }`}
      >
        {" "}
        <div
          className="flex flex-row gap-1 justify-start items-center
          align-center max-w-full"
        >
          {NodeIcons.map((NodeIcon, i) => (
            <NodeIcon
              key={i}
              className={`font-extrabold ${isInput ? "hover:scale-110" : ""}`}
              // onClick={
              //   isInput
              //     ? undefined
              //     : (e) => {
              //         setVizConsoleVisible(true);
              //         setCurrentFocusGroup(props.id);
              //         e.preventDefault();
              //         e.stopPropagation();
              //       }
              // }
            />
          ))}
          <span className="font-light overflow-hidden text-xs">
            {" "}
            {props.data.displayName}
          </span>
        </div>
        <Handle
          type="target"
          position={vertical ? Position.Top : Position.Left}
          className="opacity-0"
        />
        <Handle
          type="source"
          position={vertical ? Position.Bottom : Position.Right}
          className="opacity-0"
        />
      </div>
    </div>
  );
};
export const executionNodeTypes = {
  node: ExecutionNodeComponent,
  module: ExecutionNodeComponent,
  namespace: ExecutionNodeComponent,
  function: ExecutionNodeComponent,
  subdag: ExecutionNodeComponent,
  dataQuality: ExecutionNodeComponent,
  group: ExecutionNodeComponent,
};
