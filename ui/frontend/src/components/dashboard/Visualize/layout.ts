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

import { VizEdge, VizNode } from "./types";

import dagre from "dagre";

// Dagre graph instance
const dagreGraph = new dagre.graphlib.Graph({ compound: true });

const dagreOptions = {
  rankdir: "TB", // Top to bottom layout (can be changed to "LR" for left-to-right)
  nodesep: 80, // Node separation
  ranksep: 100, // Rank separation
  marginx: 25,
  marginy: 25,
};

export const getLayoutedElements = (
  nodes: VizNode[],
  edges: VizEdge[],
  nodeDimensions: Map<string, { width: number; height: number }>,
  vertical: boolean
) => {
  const direction = vertical ? "TB" : "LR";

  // Configure dagre graph
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({
    ...dagreOptions,
    rankdir: direction,
  });

  // Clear previous graph state
  nodes.forEach((node) => {
    if (dagreGraph.hasNode(node.id)) {
      dagreGraph.removeNode(node.id);
    }
  });

  // Add nodes to dagre graph with their dimensions
  nodes.forEach((node) => {
    const dimensions = nodeDimensions.get(node.id) || { width: 150, height: 100 };
    dagreGraph.setNode(node.id, {
      width: dimensions.width,
      height: dimensions.height,
    });

    // Handle parent-child relationships for compound graphs
    if (node.parentNode) {
      dagreGraph.setParent(node.id, node.parentNode);
    }
  });

  // Add edges to dagre graph
  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  // Calculate layout
  dagre.layout(dagreGraph);

  // Apply layout to nodes
  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    const dimensions = nodeDimensions.get(node.id) || { width: 150, height: 100 };

    // Update node position and dimensions
    node.position = {
      x: nodeWithPosition.x - dimensions.width / 2, // Center the node
      y: nodeWithPosition.y - dimensions.height / 2, // Center the node
    };
    node.data.dimensions = {
      width: dimensions.width,
      height: dimensions.height,
    };

    return node;
  });

  // Return layouted elements (no async needed for dagre)
  return Promise.resolve({
    nodes: layoutedNodes,
    edges: edges,
  });
};
