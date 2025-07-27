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

import { DAGNode } from "../components/dashboard/Visualize/types";
import {
  CodeArtifact,
  DAGTemplateWithData,
  NodeTemplate,
} from "../state/api/friendlyApi";

export const getNodesProducedByFunction = (
  dag: DAGTemplateWithData,
  codeArtifact: CodeArtifact
): NodeTemplate[] => {
  // All nodes that are produced by the function
  const producedByFunction = dag.nodes.filter((node) => {
    return node.code_artifacts?.indexOf(codeArtifact?.id || -1) != -1; // Sloppy way to check if we have it
  });
  return producedByFunction;

  //   const intermediate = producedByFunction.filter((node) => {
  //     const dependencies = node.dependencies as string[];
  //     return (
  //       // if all dependencies are produced by the function
  //       // then its not an intermediate node
  //       dependencies.filter((dependency) => {
  //         return producedByFunction.map((i) => i.name).indexOf(dependency) != -1;
  //       }).length > 0
  //     );
  //   });

  //   // Upstream nodes are all those that are depended on by the intermediate nodes
  //   const upstream = producedByFunction.flatMap((node) => {
  //     return dag.nodes.filter((otherNode) => {
  //       const dependencies = node.dependencies as string[];
  //       return (
  //         producedByFunction.map((i) => i.name).indexOf(otherNode.name) == -1 &&
  //         dependencies.includes(otherNode.name)
  //       );
  //     });
  //   });
  //   // Downstream nodes are all those that depend on any intermediate nodes

  //   return { upstream, intermediate, sinks };
};

export const getDirectlyUpstreamNodes = (
  dag: DAGTemplateWithData,
  codeArtifact: CodeArtifact
): NodeTemplate[] => {
  const nodesProducedByFunction = getNodesProducedByFunction(dag, codeArtifact);
  const upstream = nodesProducedByFunction.flatMap((node) => {
    return dag.nodes.filter((otherNode) => {
      const dependencies = node.dependencies as string[];
      return (
        nodesProducedByFunction.map((i) => i.name).indexOf(otherNode.name) ==
          -1 && dependencies.includes(otherNode.name)
      );
    });
  });
  return upstream;
};

export const groupMap = (nodes: DAGNode[]) => {
  /**
   * Groups nodes by their name
   * Note that this is required as we produce all possible supersets of nodes
   */
  const map = new Map<string, DAGNode[]>();
  for (const node of nodes) {
    const key = node.name;
    if (map.has(key)) {
      map.get(key)?.push(node);
    } else {
      map.set(key, [node]);
    }
  }
  return map;
};

export const getAllUpstreamNodes = (
  startNodes: DAGNode[],
  includeSelf: boolean,
  allNodes: DAGNode[]
): DAGNode[] => {
  // Get a map of node names to possible implementations
  const allNodeImplementations = groupMap(allNodes);
  const upstream = new Set<string>(startNodes.map((n) => n.name));
  const queue = [...startNodes];
  while (queue.length > 0) {
    const currentNode = queue.pop() as DAGNode;
    for (const dependency of currentNode.nodeTemplate.dependencies || []) {
      if (!upstream.has(dependency)) {
        const possibleUpstreamNodes =
          allNodeImplementations.get(dependency) ?? [];
        possibleUpstreamNodes.forEach((n) => {
          queue.push(n);
        });
        upstream.add(dependency);
      }
    }
  }
  const filterFunc = includeSelf
    ? () => true
    : (n: string) => !startNodes.map((node) => node.name === n).some((i) => i);
  return (
    Array.from(upstream)
      .filter(filterFunc)
      // Get all possible implementations of the node
      // If its not here (probably shouldn't happen) we just append an empty list
      .flatMap((nodeName) => allNodeImplementations.get(nodeName) ?? [])
  );
};

export const getAllDownstreamNodes = (
  startNodes: DAGNode[],
  includeSelf: boolean,
  allNodes: DAGNode[]
): DAGNode[] => {
  const allNodeImplementations = groupMap(allNodes);
  const reverseMap = new Map<string, Set<string>>(); // Map of nodes => nodes that depend on them
  const downstream = new Set<string>(startNodes.map((n) => n.name));
  for (const n of allNodes) {
    for (const dependency of n.nodeTemplate.dependencies || []) {
      const depSet = reverseMap.get(dependency) || new Set<string>();
      depSet.add(n.name);
      reverseMap.set(dependency, depSet);
    }
  }
  const queue = [...startNodes];
  while (queue.length > 0) {
    const currentNode = queue.pop();
    if (currentNode === undefined) {
      throw Error("this shouldn't happen");
    }
    const dependencies = reverseMap.get(currentNode.name) || new Set<string>();
    for (const dependency of Array.from(dependencies)) {
      if (!downstream.has(dependency)) {
        downstream.add(dependency);
        const possibleImplementations =
          allNodeImplementations.get(dependency) || [];
        possibleImplementations.forEach((n) => {
          queue.push(n);
        });
      }
    }
  }
  const filterFunc = includeSelf
    ? () => true
    : (n: string) => !startNodes.map((node) => node.name === n).some((i) => i);

  return Array.from(downstream.values())
    .filter(filterFunc)
    .flatMap((name) => allNodeImplementations.get(name) || []);
};
