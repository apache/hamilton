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

/**
 * Lay out nodes using dagre's compound graph support.
 *
 * dagre natively supports compound (clustered) graphs via setParent().
 * Group nodes are added without explicit dimensions — dagre computes
 * their size from their children. Leaf nodes get their measured dimensions.
 * All edges are included regardless of group boundaries.
 *
 * Positions from dagre are center-based; we convert to top-left for ReactFlow.
 * Child positions are made relative to their parent for ReactFlow's nested
 * node model.
 */
export const getLayoutedElements = (
  nodes: VizNode[],
  edges: VizEdge[],
  nodeDimensions: Map<string, { width: number; height: number }>,
  vertical: boolean
) => {
  const g = new dagre.graphlib.Graph({ compound: true });
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({
    rankdir: vertical ? "TB" : "LR",
    nodesep: 50,
    ranksep: 80,
    marginx: 20,
    marginy: 20,
  });

  // Determine which nodes are groups (have children)
  const childIds = new Set(
    nodes.filter((n) => n.parentNode).map((n) => n.parentNode!)
  );

  // Add all nodes
  nodes.forEach((node) => {
    if (childIds.has(node.id)) {
      // Group node: set a minimal label so dagre knows it exists,
      // but don't set width/height — dagre will compute from children.
      // We set clusterLabelPos to push the label to the top.
      g.setNode(node.id, { clusterLabelPos: "top" });
    } else {
      // Leaf node: use measured dimensions
      const dims = nodeDimensions.get(node.id) || { width: 150, height: 50 };
      g.setNode(node.id, { width: dims.width, height: dims.height });
    }
  });

  // Set parent relationships
  nodes.forEach((node) => {
    if (node.parentNode) {
      g.setParent(node.id, node.parentNode);
    }
  });

  // Add all edges (dagre handles cross-cluster edges)
  edges.forEach((edge) => {
    if (g.hasNode(edge.source) && g.hasNode(edge.target)) {
      g.setEdge(edge.source, edge.target);
    }
  });

  // Run layout
  dagre.layout(g);

  // Collect absolute center positions from dagre
  const absoluteCenters = new Map<
    string,
    { x: number; y: number; width: number; height: number }
  >();
  nodes.forEach((node) => {
    const dagreNode = g.node(node.id);
    if (dagreNode) {
      absoluteCenters.set(node.id, {
        x: dagreNode.x,
        y: dagreNode.y,
        width: dagreNode.width,
        height: dagreNode.height,
      });
    }
  });

  // Convert to ReactFlow positions (top-left, relative to parent)
  const layoutedNodes = nodes.map((node) => {
    const center = absoluteCenters.get(node.id);
    if (!center) {
      return {
        ...node,
        position: { x: 0, y: 0 },
      };
    }

    // Convert center to top-left
    let x = center.x - center.width / 2;
    let y = center.y - center.height / 2;

    // Make relative to parent if nested
    if (node.parentNode) {
      const parentCenter = absoluteCenters.get(node.parentNode);
      if (parentCenter) {
        const parentTopLeftX = parentCenter.x - parentCenter.width / 2;
        const parentTopLeftY = parentCenter.y - parentCenter.height / 2;
        x -= parentTopLeftX;
        y -= parentTopLeftY;
      }
    }

    return {
      ...node,
      position: { x, y },
      data: {
        ...node.data,
        dimensions: { width: center.width, height: center.height },
      },
    };
  });

  return Promise.resolve({
    nodes: layoutedNodes,
    edges: edges,
  });
};
