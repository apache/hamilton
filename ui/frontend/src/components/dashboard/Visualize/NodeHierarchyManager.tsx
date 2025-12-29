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

import { Switch } from "@headlessui/react";
import { DAGNode, NodeGroupingState, TerminalVizNodeType } from "./types";
import { classNames } from "../../../utils";

export const GROUPING_FUNCTION_OPTIONS = [
  {
    defaultGroupby: false,
    displayName: "module",
    groupSpecName: "module" as TerminalVizNodeType,
    assignGroup: (node: DAGNode) => {
      // return undefined
      if (node.nodeTemplate.classifications.includes("input")) {
        return undefined;
      }
      // TODO -- make this work for more than just function
      return node.codeArtifact?.name.split(".").slice(0, -1).join(".");
    },
  },
  {
    defaultGroupby: false,
    displayName: "namespace (subdag)",
    groupSpecName: "subdag" as TerminalVizNodeType,
    assignGroup: (node: DAGNode) => {
      const nameSplit = node.name.split(".");
      if (nameSplit.length > 1) {
        return nameSplit.slice(0, nameSplit.length - 1).join(".");
      }
    },
  },
  {
    defaultGroupby: false,
    displayName: "defining function",
    groupSpecName: "function" as TerminalVizNodeType,
    assignGroup: (node: DAGNode) => {
      return node.codeArtifact?.name || undefined;
    },
  },
  //   {
  //     displayName: "data quality source",
  //     groupSpecName: "dataQuality" as TerminalVizNodeType,
  //     assignGroup: (node: AugmentedHamiltonNode) => {
  //       const tags = node.tags as any;
  //       if (
  //         tags !== undefined &&
  //         tags["hamilton.data_quality.source_node"] !== undefined
  //       ) {
  //         return tags["hamilton.data_quality.source_node"];
  //       }
  //       return node.name;
  //     },
  //   },
] as {
  displayName: string;
  groupSpecName: TerminalVizNodeType;
  assignGroup: (node: DAGNode) => string | undefined;
  defaultGroupby?: boolean;
}[];

export const ToggleSwitch = (props: {
  checked: boolean;
  setChecked: (checked: boolean) => void;
}) => {
  return (
    <Switch
      checked={props.checked}
      onChange={props.setChecked}
      className="group relative inline-flex h-5 w-10 flex-shrink-0 cursor-pointer items-center justify-center rounded-full focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2"
    >
      <span className="sr-only">Use setting</span>
      <span
        aria-hidden="true"
        className="pointer-events-none absolute h-full w-full rounded-md bg-white"
      />
      <span
        aria-hidden="true"
        className={classNames(
          props.checked ? "bg-dwlightblue" : "bg-gray-200",
          "pointer-events-none absolute mx-auto h-4 w-9 rounded-full transition-colors duration-200 ease-in-out"
        )}
      />
      <span
        aria-hidden="true"
        className={classNames(
          props.checked ? "translate-x-5" : "translate-x-0",
          "pointer-events-none absolute left-0 inline-block h-5 w-5 transform rounded-full border border-gray-200 bg-white shadow ring-0 transition-transform duration-200 ease-in-out"
        )}
      />
    </Switch>
  );
};

type NodeHierarchyManagerProps = {
  nodeGroupingState: NodeGroupingState[];
  setNodeGroupingState: (nodeGroupingState: NodeGroupingState[]) => void;
};

export const NodeHierarchyManager = (props: NodeHierarchyManagerProps) => {
  return (
    <div className="bg-white/90">
      <h1 className="font-semibold p-1 text-gray-800 ">Node grouping</h1>
      <div className="space-y-5 p-1 rounded-md">
        {props.nodeGroupingState.map(
          ({ displayName, displayGroup, displaySubgroups }, i) => {
            return (
              <div className="flex flex-row items-center gap-2 text-xs" key={i}>
                <span className="text-gray-500">{"group"}</span>
                <ToggleSwitch
                  checked={displayGroup}
                  setChecked={(checked) => {
                    const newNodeGroupingState = [
                      ...props.nodeGroupingState.map((i) => ({ ...i })),
                    ];
                    newNodeGroupingState[i].displayGroup = checked;
                    // We can't collapse subgroups if we can't display group
                    if (!checked) {
                      newNodeGroupingState[i].displaySubgroups = true;
                    }
                    props.setNodeGroupingState(newNodeGroupingState);
                  }}
                />
                <span className="text-gray-500">{"collapse"}</span>
                <ToggleSwitch
                  checked={!displaySubgroups}
                  setChecked={(checked) => {
                    const newNodeGroupingState = [
                      ...props.nodeGroupingState.map((i) => ({ ...i })),
                    ];
                    newNodeGroupingState[i].displaySubgroups = !checked;
                    if (checked) {
                      newNodeGroupingState[i].displayGroup = true;
                    }
                    props.setNodeGroupingState(newNodeGroupingState);
                  }}
                />

                <span className="text-gray-700 font-semibold">
                  {" "}
                  <span className="font-normal">by</span> {displayName}
                </span>
              </div>
            );
          }
        )}
      </div>
    </div>
  );
};
