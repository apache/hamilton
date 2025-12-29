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

import {
  DAGRunWithData,
  DAGTemplateWithData,
  NodeRunWithAttributes,
} from "../../../state/api/friendlyApi";
import {
  DAGNode,
  DEFAULT_GROUP_SPEC_NAME,
  GroupSpec,
  NodeInteractionHook,
  TerminalVizNodeType,
  VizEdge,
  VizNode,
  VizNodeType,
  VizType,
} from "./types";

import {
  createContext,
  useContext,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  NodeChange,
  Panel,
  Position,
  ReactFlow,
  ReactFlowProvider,
  getBezierPath,
  useEdgesState,
  useNodesState,
  useStore,
} from "reactflow";

// Leave this in...
import "reactflow/dist/base.css";
import Highlight, { defaultProps } from "prism-react-renderer";
import dracula from "prism-react-renderer/themes/vsLight";
import {
  getArtifactTypes,
  iconForGroupSpecName,
  iconsForNodes,
  nodeKey,
} from "./utils";
import { getAdapterIcon } from "../../../utils";
import {
  GROUPING_FUNCTION_OPTIONS,
  NodeHierarchyManager,
} from "./NodeHierarchyManager";
import { useSearchParams } from "react-router-dom";
import { getLayoutedElements } from "./layout";
import { NodeVizConsole } from "./VizConsole";
import { MultiProjectVersionSelector } from "../../common/ProjectVersionSelector";
import { Legend } from "./Legend";
import { extractAllCodeContents } from "../../../utils/codeExtraction";
import {
  getAllDownstreamNodes,
  getAllUpstreamNodes,
} from "../../../utils/dagUtils";

import { executionNodeTypes } from "./DAGRun";

/**
 * Augmented node -- this allows us to
 */
type DAGVisualizeProps = {
  templates: DAGTemplateWithData[]; // Base templates to visualize
  runs: DAGRunWithData[] | undefined; // Runs to visualize, if these are undefined, we don't have run data
  // Runs and templates will have the same lenth
  nodeInteractions?: {
    onNodeGroupEnter?: NodeInteractionHook;
    onNodeGroupLeave?: NodeInteractionHook;
    onNodeGroupClick?: NodeInteractionHook;
    onNodeGroupDoubleClick?: NodeInteractionHook;
  };
  vizType: VizType;
  height?: string;
  enableLineageView: boolean;
  enableVizConsole: boolean; // Whether to enable the viz console on the side
  defaultGroupedTypes?: { [key: string]: boolean };
  displayLegend: boolean;
  enableGrouping: boolean;
  displayMiniMap?: boolean;
  displayControls?: boolean;
  nodeFilter?: (node: DAGNode) => boolean; // Filter nodes
  vertical?: boolean;
};

const SelectedNodesContext = createContext<{
  upstreamNodes: Map<string, DAGNode>;
  downstreamNodes: Map<string, DAGNode>;
  nodes: Map<string, DAGNode>;
  setCurrentFocusGroup: (value: string | undefined) => void;
  selectedDAGIndices: Set<number>;
}>({
  upstreamNodes: new Map(),
  downstreamNodes: new Map(),
  nodes: new Map(),
  setCurrentFocusGroup: () => void 0,
  selectedDAGIndices: new Set(),
});

const getStateContext = (
  upstreamNodes: Map<string, DAGNode>,
  downstreamNodes: Map<string, DAGNode>,
  selectedNodes: Map<string, DAGNode>,
  nodes: DAGNode[],
  selectedDAGIndices: Set<number>
) => {
  const out = {
    inSelectedDAG: false,
    upstreamHighlighted: false,
    downstreamHighlighted: false,
    selfHighlighted: false,
    highlightMode: false,
  };
  nodes.forEach((node) => {
    if (upstreamNodes.has(nodeKey(node))) {
      out.upstreamHighlighted = true;
    }
    if (downstreamNodes.has(nodeKey(node))) {
      out.downstreamHighlighted = true;
    }
    if (selectedNodes.has(nodeKey(node))) {
      out.selfHighlighted = true;
    }
    if (selectedNodes.size > 0) {
      out.highlightMode = true;
    }
    if (selectedDAGIndices.has(node.dagIndex)) {
      out.inSelectedDAG = true;
    }
  });
  return out;
};

export const NodeControlContext = createContext<{
  collapseGroup: (groupKey: string) => void;
  expandGroup: (groupKey: string) => void;
  collapsedGroups: Set<string>;
  displayAnything: boolean;
  setVizConsoleVisible: (value: boolean) => void;
  vertical: boolean;
}>({
  collapseGroup: () => void 0,
  expandGroup: () => void 0,
  collapsedGroups: new Set(),
  displayAnything: true,
  setVizConsoleVisible: () => void 0,
  vertical: false,
});

/**
 * Type for augmented hamilton node with extra information we might need
 */

/**
 * Converts a list of group specs to a key
 * @param groupSpec
 * @returns
 */
const convertGroupSpecsToKey = (groupSpec: GroupSpec[]): string | undefined => {
  const out = groupSpec
    .filter((spec) => spec.groupName !== undefined)
    .map((spec) => {
      return `${spec.groupSpecName}=${spec.groupName}`;
    })
    .join("::");
  if (out === "") {
    return undefined;
  }
  return out;
};

/**
 * Utility function to group the node by name.
 */
const groupByNodeName = {
  groupSpecName: DEFAULT_GROUP_SPEC_NAME,
  assignGroup: (node: DAGNode) => {
    return node.nodeTemplate.name;
  },
  displayGroup: true,
  displaySubgroups: true,
};

/**
 * Groups nodes by name. E.G. all implementations of a node will fit into one group.
 * In a single DAG, this should be a map of names to list of length 1.
 * @param nodes list of nodes to group
 * @param assignGroup function to assign groups to nodes
 * @returns A list of node -> resolved groups
 */
const assignGroupsToNodes = (
  nodes: DAGNode[],
  groupingFunctions: {
    groupSpecName: TerminalVizNodeType;
    assignGroup: (node: DAGNode) => string | undefined;
    displayGroup: boolean;
    displaySubgroups: boolean;
  }[]
): [DAGNode, GroupSpec[]][] => {
  return nodes.map((node) => {
    let hitTerminal = false;
    const groups = groupingFunctions.map((f) => {
      // If we don't want to display the group, then
      // This guy just returns null
      let groupName = f.assignGroup(node);

      if (!f.displayGroup || hitTerminal || groupName === "") {
        groupName = undefined;
      }

      if (f.displayGroup && !f.displaySubgroups && !(groupName === undefined)) {
        hitTerminal = true;
      }
      return {
        groupName: groupName,
        groupSpecName: f.groupSpecName,
        isTerminal: f.displayGroup && !f.displaySubgroups,
      };
    });
    return [node, groups];
  });
};

/**
 * Converts a list of nodes with their groups to nodes and edges.
 * This works in the following way:
 * For each group slot:
 *     For each node:
 *         -> If a group doesn't exist with that path, create it
 *         -> If a group does exist with that path, add the node to it
 *         -> Add a dependency between that node and its dependency nodes
 * Note that there's an implied node grouping of "name" -- anything with the same
 * node name will be grouped in a different way and be visualized as one (potentially with ways of indicating it)
 * This is to allow for DAG comparison.
 *
 * In the case that node groups are mutually disjoint, we may have multiple sections of the same "group". This can get
 * messy, but in reality, most nodes will be grouped in a "logical" way. TBD how this will actually look.
 *
 * Note that this doesn't currently work in the case of nested subdags :/ but I think we can figure this out by making
 * the number of classes more dynamic (or just allowing, say, n subdags)
 *
 * @param groupClasses -- list of group class order to use
 * @param nodesWithGroups -- list of nodes with their groups
 * @param collapsedGroupKeys -- list of group keys to collapse.
 * This means that anything below this just gets a simple label.
 * furthermore, any node in these groups gets replaced by this one for edges
 * @returns
 */
const convertToVizNodesAndEdges = (
  groupClasses: {
    groupSpecName: string;
    displayGroup: boolean;
    displaySubgroups: boolean;
  }[],
  nodesWithGroups: [DAGNode, GroupSpec[]][],
  collapsedGroupKeys: Set<string>,
  vertical: boolean
): [VizNode[], VizEdge[]] => {
  const vizNodesGroupedByKey = new Map<string, VizNode>();
  const nodeGroupIndex = new Map<string, { node: DAGNode; key: string }[]>();
  groupClasses.forEach((groupClass, index) => {
    nodesWithGroups.forEach(([node, groups]) => {
      // We want a unique key for each group
      // This is the group up until that point
      const groupKey = convertGroupSpecsToKey(groups.slice(0, index + 1));
      if (groupKey === undefined) {
        return;
      }
      // statement, saying if the group key is prefixed by any of the collapsed group keys, then we skip it
      // This is because we want to collapse the group

      const collapsed = Array.from(collapsedGroupKeys).some(
        (collapsedGroupKey) =>
          groupKey.startsWith(collapsedGroupKey) &&
          groupKey.replace(collapsedGroupKey, "").startsWith("::") && // This is to make sure we don't collapse the wrong thing
          groupKey !== collapsedGroupKey
      );

      // We start off assuming its a group type
      let type: VizNodeType = "group";
      // If the class is a default (E.G. its an individual node)
      // Then we can assume its a transform
      if (groupClass.groupSpecName === DEFAULT_GROUP_SPEC_NAME) {
        type = "node";
        const nodeGroups = nodeGroupIndex.get(node.name) || [];
        nodeGroups.push({ node: node, key: groupKey });
        nodeGroupIndex.set(node.name, nodeGroups);
      }
      // If the group doesn't exist/resolve to anything, we skip it
      if (groups[index].groupName === undefined) {
        return;
      }

      if (groups[index].isTerminal) {
        type = groups[index].groupSpecName;
      }
      // Let's see if we already haved the viz node data
      const vizNodeData = vizNodesGroupedByKey.get(groupKey);
      // Then we get the group key of the parent so we can set a pointer
      // The parent will always have the same group spec without the last one
      const parentGroupKey =
        index !== 0
          ? convertGroupSpecsToKey(groups.slice(0, index))
          : undefined;
      // If we haven't seen this then we want to create a node
      if (vizNodeData === undefined) {
        const displayName =
          groups[index].groupSpecName === DEFAULT_GROUP_SPEC_NAME
            ? node.name
            : `${groups[index].groupName}`;
        const newNode = {
          type: type as VizNodeType,
          id: groupKey,
          data: {
            nodes: [node],
            dimensions: { width: 0, height: 0 },
            displayName: displayName,
            level: 0,
            groupSpec: groups[index],
            groupName: groupKey,
            collapsed,
          },
          parentNode: parentGroupKey === node.name ? undefined : parentGroupKey,
          // TODO -- I don't think we use this well in the rest of the file
          // Ensure this cascades down, or get rid of it
          targetPosition: vertical ? Position.Top : Position.Left,
          sourcePosition: vertical ? Position.Bottom : Position.Right,
          position: { x: 0, y: 0 },
        };
        // Finally we add this to the map so we can add later
        vizNodesGroupedByKey.set(groupKey, newNode);
        // Otherwise we just add this to the node
      } else {
        // In this case we just add it to the nodes list
        vizNodeData.data.nodes.push(node);
      }
    });
  });
  // We already have our output nodes
  // Now we just need to remove any groups of one to declutter the viz
  const outputNodes = Array.from(vizNodesGroupedByKey.values()); //.filter(
  // (vizNode) => !(vizNode.type === "group" && vizNode.data.nodes.length == 1)
  // );
  // Now we need to add the edges
  const seenEdges = new Set<string>();
  // We only want to add an edge once
  const edgeKey = (source: string, target: string) => {
    return `${source}::${target}`;
  };
  // So we only add it if we haven't seen it
  const outputEdges = nodesWithGroups
    .flatMap(([node, groups]) => {
      const groupKey = convertGroupSpecsToKey(groups) as string;
      const dagIndex = node.dagIndex;
      return (node.nodeTemplate.dependencies || []).map((depName) => {
        const possibilities = nodeGroupIndex.get(depName) || [];
        const dep = possibilities.find(
          (p) => p.node.dagIndex === dagIndex
        )?.key;
        if (dep !== undefined && dep !== groupKey) {
          const key = edgeKey(dep, groupKey);
          if (!seenEdges.has(key)) {
            seenEdges.add(key);
            return {
              id: key,
              source: dep,
              target: groupKey,
              markerEnd: {
                type: MarkerType.Arrow,
              },
              type: "custom",
              data: {
                sourceNodes: vizNodesGroupedByKey.get(dep)?.data.nodes || [],
                targetNodes:
                  vizNodesGroupedByKey.get(groupKey)?.data.nodes || [],
              },
            };
          }
        } else {
          console.log(
            "Couldn't find dep",
            depName,
            "for node",
            node.name,
            nodesWithGroups
          );
        }
      });
    })
    .filter((item) => item !== undefined) as VizEdge[];
  return [outputNodes, outputEdges];
};

export const sortVizNodesAndAddLevels = (nodes: VizNode[]) => {
  const nodeSet = new Map<string, VizNode>(
    nodes.map((node) => [node.id, node])
  );
  const allNodes = new Map(nodeSet);
  const sortedNodes = [] as VizNode[];
  while (nodeSet.size > 0) {
    const nodeCandidates = Array.from(nodeSet);
    nodeCandidates.forEach(([name, vizNode]) => {
      if (vizNode.parentNode === undefined) {
        vizNode.data.level = 0;
        sortedNodes.push(vizNode);
        nodeSet.delete(name);
      } else {
        if (nodeSet.has(vizNode.parentNode)) {
          return;
        }
        vizNode.data.level =
          (allNodes.get(vizNode.parentNode) as VizNode).data.level + 1;
        sortedNodes.push(vizNode);
        nodeSet.delete(name);
      }
    });
  }
  return sortedNodes;
};

export const filterOutGroupsOfOne = (nodes: VizNode[]) => {
  // Dictionaries of groups of one
  const groupsOfOne = new Map(
    nodes
      .filter(
        (vizNode) =>
          vizNode.type === "group" &&
          new Set(vizNode.data.nodes.map((n) => n.name)).size == 1
      )
      .map((n) => [n.id, n])
  );
  const out = nodes
    .filter((n) => !groupsOfOne.has(n.id))
    .map((vizNode) => {
      while (
        vizNode.parentNode !== undefined &&
        groupsOfOne.has(vizNode.parentNode)
      ) {
        vizNode.parentNode = groupsOfOne.get(vizNode.parentNode)?.parentNode;
      }
      return vizNode;
    });
  return out;
};

const calcClasses = (
  highlightedContext: {
    upstreamHighlighted: boolean;
    downstreamHighlighted: boolean;
    selfHighlighted: boolean;
    highlightMode: boolean;
  },
  applicableClasses: (
    | "backgroundColor"
    | "textColor"
    | "borderColor"
    | "backgroundColorMuted"
    | "borderColorMuted"
    | "backgroundColorMutedHover"
    | "textColorPrimary"
  )[]
) => {
  let out = {
    backgroundColor: "",
    textColor: "",
    borderColor: "",
    backgroundColorMuted: "",
    borderColorMuted: "",
    backgroundColorMutedHover: "",
    textColorPrimary: "",
  };
  if (highlightedContext.selfHighlighted) {
    out = {
      backgroundColor: "bg-green-500",
      textColor: "text-white",
      borderColor: "border-green-500",
      backgroundColorMuted: "bg-green-500/80",
      borderColorMuted: "border-green-500/80",
      backgroundColorMutedHover: "hover:bg-green-500/5",
      textColorPrimary: "text-green-500",
    };
  } else if (highlightedContext.upstreamHighlighted) {
    out = {
      backgroundColor: "bg-dwred",
      textColor: "text-white",
      borderColor: "border-dwred",
      backgroundColorMuted: "bg-dwred/60",
      borderColorMuted: "border-dwred/60",
      backgroundColorMutedHover: "hover:bg-dwred/5",
      textColorPrimary: "text-dwred",
    };
  } else if (highlightedContext.downstreamHighlighted) {
    out = {
      backgroundColor: "bg-dwlightblue",
      textColor: "text-white",
      borderColor: "border-dwlightblue",
      backgroundColorMuted: "bg-dwlightblue/60",
      borderColorMuted: "border-dwlightblue/60",
      backgroundColorMutedHover: "hover:bg-dwlightblue/5",
      textColorPrimary: "text-dwlightblue",
    };
  } else if (highlightedContext.highlightMode) {
    out = {
      backgroundColor: "bg-gray-400",
      textColor: "text-white",
      borderColor: "border-gray-400",
      backgroundColorMuted: "bg-gray-400/60",
      borderColorMuted: "border-gray-400/60",
      backgroundColorMutedHover: "hover:bg-gray-400/5",
      textColorPrimary: "text-gray-400",
    };
  } else {
    out = {
      backgroundColor: "bg-dwdarkblue",
      textColor: "text-white",
      borderColor: "border-dwdarkblue",
      backgroundColorMuted: "bg-dwdarkblue/60",
      borderColorMuted: "border-dwdarkblue/60",
      backgroundColorMutedHover: "hover:bg-dwdarkblue/5",
      textColorPrimary: "text-dwdarkblue",
    };
  }

  return applicableClasses.map((className) => out?.[className]).join(" ");
};

export const extractArtifactTypes = (nodes: DAGNode[]): Set<string> => {
  const nodesWithArtifacts = nodes.filter(
    (n) =>
      n.nodeTemplate.classifications.includes("data_loader") ||
      n.nodeTemplate.classifications.includes("data_saver")
  );

  const artifactTypes = getArtifactTypes(nodesWithArtifacts);
  return artifactTypes;
};

const BaseNodeComponent = (props: {
  data: {
    nodes: DAGNode[];
    displayName: string;
    collapsed: boolean;
    groupSpec: GroupSpec;
  };
  id: string;
}) => {
  const { displayAnything, setVizConsoleVisible, vertical } =
    useContext(NodeControlContext);

  const NodeIcons =
    props.data.groupSpec.groupSpecName === "node"
      ? iconsForNodes(props.data.nodes)
      : [iconForGroupSpecName(props.data.groupSpec.groupSpecName)];

  const isInput = props.data.nodes
    .map((item) => item.nodeTemplate.classifications.includes("input"))
    .some((i) => i);
  const isExternalToSubdag = props.data.nodes
    .map((item) =>
      item.nodeTemplate.classifications.includes("external_to_subdag")
    )
    .some((i) => i);
  const hidden = props.data.collapsed;
  const {
    upstreamNodes,
    downstreamNodes,
    nodes: selectedNodes,
    setCurrentFocusGroup,
    selectedDAGIndices,
  } = useContext(SelectedNodesContext);

  const highlightedContext = getStateContext(
    upstreamNodes,
    downstreamNodes,
    selectedNodes,
    props.data.nodes,
    selectedDAGIndices
  );

  let colorClasses = isInput
    ? calcClasses(highlightedContext, ["textColorPrimary", "borderColor"]) +
      " border border-2 bg-white"
    : calcClasses(highlightedContext, [
        "backgroundColor",
        "textColor",
        "borderColor",
      ]) + " border border-2";

  if (isExternalToSubdag && !isInput) {
    colorClasses = `${colorClasses} opacity-50`;
  }

  const outlineColorClasses = calcClasses(highlightedContext, ["borderColor"]);

  const iconClasses = calcClasses(highlightedContext, ["textColorPrimary"]);

  const artifactTypes = extractArtifactTypes(props.data.nodes);

  const hasArtifact = artifactTypes.size > 0;

  const backgroundHoverClasses = calcClasses(highlightedContext, [
    "backgroundColorMutedHover",
  ]);

  return (
    <div
      className={`${
        highlightedContext.inSelectedDAG ? "" : "opacity-20"
      } group flex flex-col gap-3 items-center cursor-cell ${
        hasArtifact ? "border border-dashed " : " "
      } rounded-lg p-1 ${
        displayAnything ? "" : "invisible"
      } ${outlineColorClasses} ${backgroundHoverClasses}`}
      onClick={() => {
        if (highlightedContext.selfHighlighted) {
          setCurrentFocusGroup(undefined);
        } else {
          setCurrentFocusGroup(props.id);
        }
      }}
    >
      {artifactTypes.size > 0 ? (
        <div className="flex flex-row">
          {Array.from(artifactTypes).map((artifactType, i) => {
            const Icon = getAdapterIcon(artifactType);
            return (
              <Icon
                className={`text-5xl group-hover:text-opacity-80 ${iconClasses}`}
                key={i}
              />
            );
          })}
        </div>
      ) : (
        <></>
      )}
      <div
        className={` ${colorClasses}  group-hover:opacity-80 h-max w-max text-sm p-1 rounded-md cursor-cell ${
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
              onClick={
                isInput
                  ? undefined
                  : (e) => {
                      setVizConsoleVisible(true);
                      setCurrentFocusGroup(props.id);
                      e.preventDefault();
                      e.stopPropagation();
                    }
              }
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

export const CodeView: React.FC<{
  fnContents: string;
  displayFnExpand?: boolean;
  inDAGView?: boolean;
}> = (props) => {
  return (
    <div
      className={`${
        props.inDAGView ? "text-2xs max-w-2xl" : ""
      } bg-white/80 p-2`}
    >
      <Highlight
        {...defaultProps}
        theme={dracula}
        code={props.fnContents}
        language="python"
      >
        {({ className, style, tokens, getLineProps, getTokenProps }) => {
          const styleToRender = {
            ...style,
            backgroundColor: "transparent",
            "word-break": "break-all",
            "white-space": "pre-wrap",
          };
          className += "";
          return (
            <pre className={className} style={styleToRender}>
              {tokens.map((line, i) => (
                // eslint-disable-next-line react/jsx-key
                <div {...getLineProps({ line, key: i })}>
                  {line.map((token, key) => (
                    // eslint-disable-next-line react/jsx-key
                    <span hidden={false} {...getTokenProps({ token, key })} />
                  ))}
                </div>
              ))}
            </pre>
          );
        }}
      </Highlight>
    </div>
  );
};

const FunctionNodeComponent = (props: {
  data: {
    nodes: DAGNode[];
    displayName: string;
    collapsed: boolean;
    groupSpec: GroupSpec;
  };
  id: string;
}) => {
  const { displayAnything, setVizConsoleVisible, vertical } =
    useContext(NodeControlContext);

  const NodeIcons =
    props.data.groupSpec.groupSpecName === "node"
      ? iconsForNodes(props.data.nodes)
      : [iconForGroupSpecName(props.data.groupSpec.groupSpecName)];

  const isInput = props.data.nodes
    .map((item) => item.nodeTemplate.classifications.includes("input"))
    .some((i) => i);
  const hidden = props.data.collapsed;
  const {
    upstreamNodes,
    downstreamNodes,
    nodes: selectedNodes,
    setCurrentFocusGroup,
    selectedDAGIndices,
  } = useContext(SelectedNodesContext);

  const highlightedContext = getStateContext(
    upstreamNodes,
    downstreamNodes,
    selectedNodes,
    props.data.nodes,
    selectedDAGIndices
  );

  const colorClasses = isInput
    ? calcClasses(highlightedContext, ["textColorPrimary", "borderColor"]) +
      " border border-2 bg-white"
    : calcClasses(highlightedContext, [
        "backgroundColor",
        "textColor",
        "borderColor",
      ]) + " border border-2";

  const outlineColorClasses = calcClasses(highlightedContext, ["borderColor"]);

  const iconClasses = calcClasses(highlightedContext, ["textColorPrimary"]);

  const artifactTypes = extractArtifactTypes(props.data.nodes);

  const hasArtifact = artifactTypes.size > 0;

  const backgroundHoverClasses = calcClasses(highlightedContext, [
    "backgroundColorMutedHover",
  ]);

  return (
    <div
      className={`${
        highlightedContext.inSelectedDAG ? "" : "opacity-20"
      } group flex flex-col gap-3 items-center cursor-cell ${
        hasArtifact ? "border border-dashed " : " "
      } rounded-lg p-1 ${
        displayAnything ? "" : "invisible"
      } ${outlineColorClasses} ${backgroundHoverClasses}`}
      onClick={() => {
        if (highlightedContext.selfHighlighted) {
          setCurrentFocusGroup(undefined);
        } else {
          setCurrentFocusGroup(props.id);
        }
      }}
    >
      {artifactTypes.size > 0 ? (
        <div className="flex flex-row">
          {Array.from(artifactTypes).map((artifactType, i) => {
            const Icon = getAdapterIcon(artifactType);
            return (
              <Icon
                className={`text-5xl group-hover:text-opacity-80 ${iconClasses}`}
                key={i}
              />
            );
          })}
        </div>
      ) : (
        <></>
      )}
      <div
        className={` ${colorClasses}  group-hover:opacity-80 h-max w-max text-sm p-1 rounded-md cursor-cell ${
          hidden ? "hidden" : ""
        }`}
      >
        {" "}
        <div className="flex flex-col max-w-full">
          <div className="flex flex-row justify-between">
            <div className="flex flex-row gap-1 justify-start items-center align-center">
              {NodeIcons.map((NodeIcon, i) => (
                <NodeIcon
                  key={i}
                  className={`font-extrabold ${
                    isInput ? "hover:scale-110" : ""
                  }`}
                  onClick={
                    isInput
                      ? undefined
                      : (e) => {
                          setVizConsoleVisible(true);
                          setCurrentFocusGroup(props.id);
                          e.preventDefault();
                          e.stopPropagation();
                        }
                  }
                />
              ))}
              <span className="font-light overflow-hidden text-xs pb-1">
                {" "}
                {props.data.displayName}
              </span>
            </div>
          </div>
          <div>
            <CodeView fnContents={props.data.nodes[0].codeContents || ""} />
          </div>
          {/* <pre className="text-2xs max-w-lg bg-white text-black whitespace-pre-wrap p-2" >{fn?.contents}</pre> */}
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

const GroupedNodeComponent = (props: {
  data: {
    nodes: DAGNode[];
    dimensions: { width: number; height: number };
    displayName: string;
    groupSpec: GroupSpec;
    groupName: TerminalVizNodeType;
  };
  id: string;
}) => {
  const {
    upstreamNodes,
    downstreamNodes,
    nodes: selectedNodes,
    setCurrentFocusGroup,
    selectedDAGIndices,
  } = useContext(SelectedNodesContext);

  const highlightedContext = getStateContext(
    upstreamNodes,
    downstreamNodes,
    selectedNodes,
    props.data.nodes,
    selectedDAGIndices
  );

  // E.G. module, etc...
  const { groupSpecName, groupName } = props.data.groupSpec;
  const { collapsedGroups, displayAnything, setVizConsoleVisible } =
    useContext(NodeControlContext);
  const Icon = iconForGroupSpecName(groupSpecName);
  const isCollapsedGroup = collapsedGroups.has(props.data.groupName);
  // TODO -- fix this hack
  // This is cause I'm using prefixes and some might have the same prefix
  // Really we should be filtering through nodes and passing a set down...
  // We can do this in the layouting phase, or just use the data passed in
  const shouldBeHidden = Array.from(collapsedGroups).some((group) => {
    props.data.groupName.startsWith(group) &&
      props.data.groupName.replace(group, "").startsWith("::") &&
      props.data.groupName !== group;
  });

  return (
    <div
      className={`${
        displayAnything ? "" : "invisible"
      } border-4 border-solid ${calcClasses(highlightedContext, [
        "borderColorMuted",
        "backgroundColorMutedHover",
      ])} cursor-cell rounded-lg flex gap-2 ${
        isCollapsedGroup ? "bg-gray-300" : ""
      }
        ${shouldBeHidden ? " hidden " : ""}

        `}
      style={{
        width: props.data.dimensions?.width,
        height: props.data.dimensions?.height,
      }}
      onClick={() => {
        if (highlightedContext.selfHighlighted) {
          setCurrentFocusGroup(undefined);
          return;
        }
        setCurrentFocusGroup(props.id);
      }}
    >
      <span
        className={`font-bold py-1 h-min ${
          highlightedContext.inSelectedDAG ? " " : "opacity-20"
        } ${calcClasses(highlightedContext, [
          "backgroundColorMuted",
          "textColor",
        ])} cursor-cell flex justify-between w-full overflow-hidden`}
      >
        {shouldBeHidden ? (
          <></>
        ) : (
          <>
            <div className="flex justify-start items-center max-w-full gap-2">
              <Icon
                className="font-extrabold hover:scale-110"
                onClick={(e) => {
                  setVizConsoleVisible(true);
                  setCurrentFocusGroup(props.id);
                  e.preventDefault();
                  e.stopPropagation();
                }}
              />
              <span className="font-normal  overflow-hidden text-xs">
                {" "}
                {groupName}
              </span>
            </div>
          </>
        )}
      </span>
    </div>
  );
};

const RENDER_DELAY = 500;

export default function CustomEdgeComponent({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  markerEnd,
  data,
}: {
  id: string;
  source: string;
  target: string;
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
  sourcePosition: Position;
  targetPosition: Position;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  markerEnd?: any;
  data?: {
    sourceNodes: DAGNode[];
    targetNodes: DAGNode[];
  };
}) {
  const {
    upstreamNodes,
    downstreamNodes,
    nodes: selectedNodes,
    selectedDAGIndices,
  } = useContext(SelectedNodesContext);

  const upstreamHighlighted = data?.sourceNodes
    .map(
      (n) =>
        upstreamNodes.has(nodeKey(n)) ||
        downstreamNodes.has(nodeKey(n)) ||
        selectedNodes.has(nodeKey(n))
    )
    .some((i) => i);

  const downstreamHighlighted =
    data?.targetNodes
      .map((n) => upstreamNodes.has(nodeKey(n)))
      .some((i) => i) ||
    data?.targetNodes
      .map((n) => downstreamNodes.has(nodeKey(n)))
      .some((i) => i) ||
    data?.targetNodes.map((n) => selectedNodes.has(nodeKey(n))).some((i) => i);

  const upstreamInDAG = data?.sourceNodes
    .map((n) => selectedDAGIndices.has(n.dagIndex))
    .some((i) => i);

  const downstreamInDAG = data?.targetNodes
    .map(
      (n) => selectedDAGIndices.has(n.dagIndex)
      // (upstreamNodes.has(nodeKey(n)) && selectedDAGIndices.has(n.dagIndex)) ||
      // (downstreamNodes.has(nodeKey(n)) &&
      //   selectedDAGIndices.has(n.dagIndex)) ||
      // (selectedNodes.has(nodeKey(n)) && selectedDAGIndices.has(n.dagIndex))
    )
    .some((i) => i);

  const edgeInDAG = downstreamInDAG && upstreamInDAG;
  const isFocused = upstreamHighlighted && downstreamHighlighted;
  const strokeColor = isFocused ? "rgb(55, 65, 81)" : "rgb(209, 213, 219)"; // Haven't gotten the tailwind classes to work with the stroke colors
  const strokeOpacityClass = edgeInDAG ? "opacity-80" : "opacity-40";

  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <path
      id={id}
      className={`react-flow__edge-path  ${strokeOpacityClass} stroke-1`}
      style={{
        // strokeWidth: 1,
        stroke: strokeColor,
        // strokeOpacity: 1
      }}
      d={edgePath}
      markerEnd={markerEnd}
    />
  );
}

const defaultNodeTypes = {
  node: BaseNodeComponent,
  module: BaseNodeComponent,
  namespace: BaseNodeComponent,
  function: FunctionNodeComponent,
  subdag: BaseNodeComponent,
  dataQuality: BaseNodeComponent,
  group: GroupedNodeComponent,
};

const edgeTypes = { custom: CustomEdgeComponent };

/**
 * This is a listener to figure out the node height
 * It is so that we can re-render after the node is constructed
 * Unfortunately it likely adds a ton of complexity, so we need to be careful
 * @param props
 * @returns
 */
const NodeDimensionsSetter = (props: {
  setNodeDimensions: (
    dimensions: Map<string, { height: number; width: number }>
  ) => void;
  nodeDimensions: Map<string, { height: number; width: number }>;
}) => {
  const nodesWithData = useStore((state) => {
    return Array.from(state.nodeInternals.values());
  });
  useLayoutEffect(() => {
    let anyChanges = false;
    const newNodeDimensions = new Map<
      string,
      { height: number; width: number }
    >();
    nodesWithData.forEach((node) => {
      // if (node.type === "group") {
      //   return;
      // }
      const oldDimensions = props.nodeDimensions.get(node.id);
      if (
        oldDimensions?.height !== node.height ||
        oldDimensions?.width !== node.width
      ) {
        anyChanges = true;
      }

      newNodeDimensions.set(node.id, {
        height: node.height || 0,
        width: node.width || 0,
      });
    });
    if (anyChanges) {
      props.setNodeDimensions(newNodeDimensions);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.nodeDimensions]);
  return <></>;
};

const createNodes = (
  dagTemplate: DAGTemplateWithData,
  dagRuns: DAGRunWithData[] | undefined,
  index: number
): DAGNode[] => {
  const codeArtifacts = dagTemplate.code_artifacts;

  const allCodeContents = extractAllCodeContents(codeArtifacts, dagTemplate);
  const codeArtifactsById = new Map(
    codeArtifacts.map((ca) => [ca.id as number, ca])
  );
  const nodeRunsGroupedByTemplateName = new Map<
    string,
    NodeRunWithAttributes[]
  >();
  dagRuns?.forEach((dagRun) => {
    dagRun.node_runs.forEach((nodeRun) => {
      const nodeName = nodeRun.node_template_name;
      if (!nodeRunsGroupedByTemplateName.has(nodeName)) {
        nodeRunsGroupedByTemplateName.set(nodeName, []);
      }
      nodeRunsGroupedByTemplateName.get(nodeName)?.push(nodeRun);
    });
  });
  const allCodeContentsByArtifactId = new Map<number, string>();
  allCodeContents.forEach((codeContents, i) => {
    if (codeContents !== undefined) {
      allCodeContentsByArtifactId.set(
        codeArtifacts[i].id as number,
        codeContents
      );
    }
  });

  const nodes = dagTemplate.nodes.map((nodeTemplate) => {
    // TODO -- allow for multiple, and select the primary
    const codeArtifactId = nodeTemplate.code_artifacts[0];
    return {
      nodeTemplate: nodeTemplate,
      nodeRuns: nodeRunsGroupedByTemplateName.get(nodeTemplate.name), // TODO -- use Node Runs to get this to work
      dagIndex: index,
      name: nodeTemplate.name,
      codeArtifact: codeArtifactId
        ? codeArtifactsById.get(codeArtifactId)
        : undefined, // TODO -- get this
      codeContents: codeArtifactId
        ? allCodeContentsByArtifactId.get(codeArtifactId)
        : undefined,
    };
  });
  return nodes;
};

/**
 * React component to visualize a DAG.
 * This has a few core features:
 * 1. The ability to group/ungroup nodes, including multiple hierarchies
 * 2. The ability to highlight nodes/lineage
 * 3. The ability to combine nodes from multiple DAGs to do comparison.
 * 4. The ability to add hooks for entering/exiting a group
 * 5. Display artifacts/other types of nodes separately
 *
 * The future idea is to add pluggable "attributes" to a node. One could:
 * - render these attributes
 * - render the diff these attributes
 * - maybe use these to group/compare?
 *
 * For now though this is meant to solve the problem of
 * visualizing a complex DAG by breaking it into hierarchy.
 *
 *
 */
export const VisualizeDAG: React.FC<DAGVisualizeProps> = (props) => {
  let allNodes = props.templates.flatMap((dagTemplate, i) => {
    return createNodes(dagTemplate, props.runs, i);
  });
  allNodes = props.nodeFilter ? allNodes.filter(props.nodeFilter) : allNodes;
  const [projectVersionIndices, setProjectVersionIndices] = useState<
    Set<number>
  >(new Set(props.templates?.map((i, index) => index) || []));
  const vertical = props.vertical || false;
  const [nodeGroupingState, setNodeGroupingState] = useState(
    GROUPING_FUNCTION_OPTIONS.map((option) => {
      return {
        ...option,
        displaySubgroups: true,
        displayGroup: Object.prototype.hasOwnProperty.call(
          props.defaultGroupedTypes || {},
          option.groupSpecName
        )
          ? (props.defaultGroupedTypes?.[option.groupSpecName] as boolean)
          : option.defaultGroupby || false,
      };
    })
  );

  const [nodeDimensions, setNodesWithDimensions] = useState<
    Map<string, { height: number; width: number }>
  >(new Map());

  const [renderingDelayState, setRenderingDelayState] = useState<
    "uninitialized" | "rendering" | "complete"
  >("uninitialized");

  useMemo(() => {
    if (renderingDelayState === "uninitialized") {
      setRenderingDelayState("rendering");
      setTimeout(() => {
        setRenderingDelayState("complete");
      }, RENDER_DELAY);
    }
  }, [renderingDelayState]);

  const triggerRerender = () => {
    setRenderingDelayState("uninitialized");
    setNodesWithDimensions(new Map());
  };
  const [collapsedGroupKeys, setCollapsedGroupKeys] = useState(
    new Set<string>([])
  );

  const [searchParams, setSearchParams] = useSearchParams();
  const currentFocusParamsRaw = searchParams.get("focus");

  const setCurrentFocusGroup = (focusGroup: string | undefined) => {
    if (focusGroup) {
      searchParams.set("focus", JSON.stringify({ group: focusGroup }));
    } else {
      searchParams.delete("focus");
    }
    setSearchParams(searchParams);
  };

  const currentFocusNodesRef = useRef<Map<string, DAGNode>>(new Map());

  // const [currentFocusNodes, setCurrentFocusNodes] = useState<
  //   Map<string, AugmentedHamiltonNode>
  // >(new Map());

  // TODO -- enable lineage on all DAGs
  // This will require:
  // 1. Using the DAG name as a prefix for the node name
  // Doing a chain operation

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const [vizConsoleVisible, setVizConsoleVisible] = useState(false);

  // This is a big hack to allow for resizing of nodes
  // We'll figure out a cleaner way of doing it'

  const groupingFunctions = [...nodeGroupingState, groupByNodeName];
  const groupClasses = groupingFunctions.map((f) => ({
    groupSpecName: f.groupSpecName,
    displayGroup: f.displayGroup,
    displaySubgroups: f.displaySubgroups,
    assignGroup: f.assignGroup,
  }));

  const parseCurrentFocusParams = (initNodes: VizNode[]) => {
    const currentFocusParams = JSON.parse(currentFocusParamsRaw || "{}");
    const currentFocusGroup = currentFocusParams.group;
    if (currentFocusGroup !== undefined) {
      return new Map(
        initNodes
          .filter((n) => n.id === currentFocusGroup)
          .flatMap((n) => n.data.nodes.map((n) => [nodeKey(n), n]))
      );
    }
    const currentFocusNode = currentFocusParams.node;
    if (currentFocusNode !== undefined) {
      return new Map(
        initNodes.flatMap(
          (vizNode) =>
            vizNode.data.nodes
              .map((n) =>
                n.name === currentFocusNode ? [nodeKey(n), n] : undefined
              )
              .filter((item) => item !== undefined) as [string, DAGNode][]
        )
      );
    }
    const currentFocusFunction = currentFocusParams.function;
    if (currentFocusFunction !== undefined) {
      return new Map(
        initNodes.flatMap(
          (vizNode) =>
            vizNode.data.nodes
              .map((n) =>
                n.codeArtifact?.name === currentFocusFunction
                  ? [nodeKey(n), n]
                  : undefined
              )
              .filter((item) => item !== undefined) as [string, DAGNode][]
        )
      );
    }
    return new Map();
  };

  useMemo(() => {
    const nodesWithGroups = assignGroupsToNodes(allNodes, groupClasses);
    const initNodes = convertToVizNodesAndEdges(
      groupClasses,
      nodesWithGroups,
      collapsedGroupKeys,
      vertical
    )[0];
    currentFocusNodesRef.current = parseCurrentFocusParams(initNodes);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentFocusParamsRaw]);

  const currentFocusNodes = currentFocusNodesRef.current;
  //   TODO -- get upstream nodes
  const upstreamNodes: Map<string, DAGNode> = new Map(
    props.templates.flatMap((template, i) => {
      return getAllUpstreamNodes(
        Array.from(currentFocusNodes.values()),
        false,
        allNodes.filter((n) => n.dagIndex === i)
      ).map((node) => {
        const augmentedNode = { ...node, dagIndex: i };
        return [nodeKey(node), augmentedNode];
      });
    })
  );

  const downstreamNodes: Map<string, DAGNode> = new Map(
    props.templates.flatMap((template, i) => {
      return getAllDownstreamNodes(
        Array.from(currentFocusNodes.values()),
        false,
        allNodes.filter((n) => n.dagIndex === i)
      ).map((node) => {
        const augmentedNode = { ...node, dagIndex: i };
        return [nodeKey(node), augmentedNode];
      });
    })
  );

  const selectedNodeContextValue = props.enableLineageView
    ? {
        upstreamNodes: upstreamNodes,
        downstreamNodes: downstreamNodes,
        nodes: currentFocusNodes,
        setCurrentFocusGroup: setCurrentFocusGroup,
        selectedDAGIndices: projectVersionIndices,
      }
    : {
        upstreamNodes: new Map<string, DAGNode>(),
        downstreamNodes: new Map<string, DAGNode>(),
        nodes: currentFocusNodes,
        setCurrentFocusGroup: () => void 0,
        selectedDAGIndices: projectVersionIndices,
      };

  useMemo(() => {
    const nodesWithGroups = assignGroupsToNodes(allNodes, groupClasses);
    const [initNodes, initEdges] = convertToVizNodesAndEdges(
      groupClasses,
      nodesWithGroups,
      collapsedGroupKeys,
      vertical
    );
    const filteredNodes = filterOutGroupsOfOne(initNodes);
    const sortedNodes = sortVizNodesAndAddLevels(filteredNodes);
    getLayoutedElements(sortedNodes, initEdges, nodeDimensions, vertical).then(
      (elements) => {
        const layoutedNodes = elements?.nodes;
        const layoutedEdges = elements?.edges;
        if (layoutedNodes === undefined || layoutedEdges === undefined) {
          return;
        }
        setNodes(layoutedNodes);
        setEdges(layoutedEdges);
      }
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodeDimensions, nodeGroupingState]);

  const height = props.height === undefined ? "h-[90vh]" : props.height;
  const shouldRender = renderingDelayState === "complete";

  const nodeTypesToUse =
    props.vizType == VizType.DAGRun ? executionNodeTypes : defaultNodeTypes;

  return (
    <>
      {props.enableVizConsole && currentFocusNodes.size > 0 && (
        <NodeVizConsole
          open={vizConsoleVisible}
          setOpen={setVizConsoleVisible}
          nodes={Array.from(currentFocusNodes.values())}
          dagTemplates={props.templates}
          // visible={vizConsoleVisible}
          // setVisible={setVizConsoleVisible}
        />
      )}
      <div
        //eslint-disable-next-line
        className={`${height} relative top-0 ${
          shouldRender ? "" : "invisible"
        }`}
      >
        <ReactFlowProvider>
          <NodeDimensionsSetter
            setNodeDimensions={setNodesWithDimensions}
            nodeDimensions={nodeDimensions}
          />
          <SelectedNodesContext.Provider value={selectedNodeContextValue}>
            <NodeControlContext.Provider
              value={{
                expandGroup: (groupName: string) => {
                  setCollapsedGroupKeys((keys) => {
                    const newKeys = new Set(keys);
                    newKeys.delete(groupName);
                    return newKeys;
                  });
                  triggerRerender();
                },
                collapseGroup: (groupName: string) => {
                  setCollapsedGroupKeys((keys) => {
                    const newKeys = new Set(keys);
                    newKeys.add(groupName);
                    return newKeys;
                  });
                  triggerRerender();
                },
                collapsedGroups: collapsedGroupKeys,
                displayAnything: shouldRender, // We have to pass this through cause react flow is weird
                setVizConsoleVisible,
                vertical: vertical,
                // nodeKeyToCodeArtifactMapping,
              }}
            >
              <div className="h-full w-full">
                <ReactFlow
                  zoomOnDoubleClick={false}
                  nodesDraggable={false}
                  nodes={nodes}
                  edges={edges}
                  onNodesChange={(changes: NodeChange[]) => {
                    onNodesChange(changes);
                    triggerRerender();
                  }}
                  onEdgesChange={onEdgesChange}
                  fitView
                  fitViewOptions={{
                    padding: 0.1,
                    minZoom: 1,
                    maxZoom: 1,
                    // duration: 0.5,
                  }}
                  minZoom={0.01}
                  maxZoom={10}
                  nodeTypes={nodeTypesToUse} // TODO -- consider allowing custom node types
                  edgeTypes={edgeTypes} // TODO -- consider allowing custom edge types
                  elementsSelectable={false}
                  proOptions={{ hideAttribution: true }}
                  onNodeClick={(event, node) => {
                    props.nodeInteractions?.onNodeGroupClick?.(node.data.nodes);
                    event.preventDefault();
                  }}
                  onNodeMouseEnter={(event, node) => {
                    props.nodeInteractions?.onNodeGroupEnter?.(node.data.nodes);
                  }}
                  onNodeMouseLeave={(event, node) => {
                    props.nodeInteractions?.onNodeGroupEnter?.(node.data.nodes);
                  }}
                >
                  <Panel position={"bottom-left"}>
                    <div className="flex flex-col gap-2 visible">
                      {props.enableGrouping && (
                        <NodeHierarchyManager
                          nodeGroupingState={nodeGroupingState}
                          setNodeGroupingState={(state) => {
                            triggerRerender();
                            setNodeGroupingState(state);
                          }}
                        />
                      )}
                      {props.displayLegend && <Legend />}
                      {props.templates.length > 1 ? (
                        <div className="py-2">
                          <MultiProjectVersionSelector
                            projectVersionsIndices={projectVersionIndices}
                            setProjectVersionsIndices={(s) =>
                              setProjectVersionIndices(s)
                            }
                            dagTemplates={props.templates}
                          />
                        </div>
                      ) : (
                        <></>
                      )}
                    </div>
                  </Panel>
                  {props.displayMiniMap || props.displayControls ? (
                    <Panel position="bottom-right">
                      {props.displayControls ? (
                        <Controls className="-translate-x-10 -translate-y-5" />
                      ) : (
                        <></>
                      )}
                      {props.displayMiniMap ? (
                        <MiniMap
                          className="-translate-x-5"
                          pannable={true}
                          ariaLabel={null}
                          // position="bottom-right"
                        />
                      ) : (
                        <></>
                      )}
                    </Panel>
                  ) : (
                    <></>
                  )}
                </ReactFlow>
              </div>
            </NodeControlContext.Provider>
          </SelectedNodesContext.Provider>
        </ReactFlowProvider>
      </div>
    </>
  );
};
