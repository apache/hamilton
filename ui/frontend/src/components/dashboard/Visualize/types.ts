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

import { Position } from "reactflow";
import {
  CodeArtifact,
  NodeRunWithAttributes,
  NodeTemplate,
} from "../../../state/api/friendlyApi";

/**
 * Augmented node that has any information we need to render/display
 * Note that this has optional node runs. If not provided, we're in static view
 */
export type DAGNode = {
  nodeTemplate: NodeTemplate;
  codeArtifact: CodeArtifact | undefined;
  codeContents: string | undefined;
  // Undefined means we don't have node run information
  // Empty array means we have node run information, but no runs
  nodeRuns: NodeRunWithAttributes[] | undefined;
  dagIndex: number;
  name: string;
};

export enum VizType {
  StaticDAG = "static_dag",
  DAGRun = "dag_run",
}

export type NodeInteractionHook = (nodes: DAGNode[]) => void;

/**
 * Vizualization node type. This is used to determine how to render
 * the node/other data about it (grouping, in particular).
 */

export type TerminalVizNodeType =
  | "node"
  | "function"
  | "subdag"
  | "input"
  | "artifact"
  | "module"
  | "dataQuality";

export type VizNodeType = TerminalVizNodeType | "group";

/**
 * Group spec. This is used to determine how to group nodes.
 * The group spec has a name, which is kind of like the class. E.G.
 * grouping by node function could have the name "function".
 */
export type GroupSpec = {
  groupName: string | undefined;
  groupSpecName: TerminalVizNodeType;
  isTerminal: boolean;
};

export const DEFAULT_GROUP_SPEC_NAME = "node" as TerminalVizNodeType;

/**
 * Node types to represent the visual nodes in the DAG.
 * Note that, due to the way reactflow represents its nodes,
 * we could have multiple overlapping for sub-flows.
 */
export type VizNode = {
  id: string;
  data: {
    displayName: string;
    nodes: DAGNode[];
    dimensions: { width: number; height: number };
    level: number; // level in the hierarchy. Starts at 0 (leaf node)
    groupSpec: GroupSpec | undefined;
    groupName: string;
  };
  parentNode?: string | undefined; // pointer to the name of the parent group
  targetPosition: Position;
  sourcePosition: Position;
  position: { x: number; y: number };
  type: VizNodeType;
};

/**
 * Edge types to represent edges in the visualization
 */
export type VizEdge = {
  id: string;
  source: string;
  target: string;
  type: "custom";
  data?: {
    sourceNodes: DAGNode[];
    targetNodes: DAGNode[];
  };
};

export type NodeGroupingState = {
  groupSpecName: TerminalVizNodeType;
  displayName: string;
  displaySubgroups: boolean;
  displayGroup: boolean;
  assignGroup: (nodes: DAGNode) => string | undefined;
};
