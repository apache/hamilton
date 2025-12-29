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

import React from "react";
import { DAGNode, VizType } from "../../Visualize/types";
import {
  DAGRunWithData,
  DAGTemplateWithData,
} from "../../../../state/api/friendlyApi";
import { DAGRunViewContext } from "../../Visualize/DAGRun";
import { VisualizeDAG } from "../../Visualize/DAGViz";

export const DAGRunView: React.FC<{
  run: DAGRunWithData;
  highlightedTasks: string[] | null;
  dagTemplate: DAGTemplateWithData;
  setHighlightedTasks: (tasks: string[] | null) => void;
  isHighlighted: boolean;
  // TODO -- merge with the waterfall chart so we don't duplicate logic
  setHighlighted: (highlighted: boolean) => void;
}> = (props) => {
  const nodeClickHook = (n: DAGNode[]) => {
    const domNode = document.getElementById(`#${n[0].name}`);
    domNode?.scrollIntoView({ behavior: "smooth", block: "center" });
  };

  return (
    <div
      className={` ${props.isHighlighted ? "bg-dwdarkblue/5" : ""}`}
      onMouseEnter={() => props.setHighlighted(true)}
      onMouseLeave={() => props.setHighlighted(false)}
    >
      <DAGRunViewContext.Provider
        value={{
          highlighedTasks: new Set(props.highlightedTasks ?? []),
        }}
      >
        <VisualizeDAG
          templates={[props.dagTemplate]}
          height="h-[500px]"
          enableVizConsole={false}
          enableLineageView={false}
          nodeInteractions={{
            onNodeGroupEnter: (nodes) => {
              props.setHighlightedTasks(nodes.map((n) => n.name));
            },
            onNodeGroupLeave: () => {
              props.setHighlightedTasks(null);
            },
            onNodeGroupClick: nodeClickHook,
          }}
          // TODO -- when we get the grouped node type
          defaultGroupedTypes={{ function: false }}
          runs={[props.run]}
          vizType={VizType.DAGRun}
          displayLegend={false}
          enableGrouping={false}
          displayControls={true}
        />
      </DAGRunViewContext.Provider>
    </div>
  );
};
