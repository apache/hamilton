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

import React, { useRef } from "react";
import {
  DAGRunWithData,
  NodeRunWithAttributes,
} from "../../../../state/api/friendlyApi";
import { Bar } from "react-chartjs-2";
import zoomPlugin from "chartjs-plugin-zoom";

import {
  Chart as ChartJS,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Filler,
  Legend,
} from "chart.js";

ChartJS.register(
  BarElement,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Legend,
  zoomPlugin
);

/**
 * Gets the color for a node
 * @param node Node to get the color for
 * @returns A tailwind bg-class reprseenting the color as well as its highlighted version
 */
const getColor = (node: NodeRunWithAttributes): [string, string, string] => {
  switch (node.status) {
    case "SUCCESS":
      return ["bg-green-500/50", "bg-green-500", "rgb(34, 197, 94, 0.5)"];
    case "FAILURE":
      return ["bg-dwred/50", "bg-dwred", "rgb(234, 85, 86, 0.5)"];
    case "UNINITIALIZED":
      return ["bg-gray-500/50", "bg-gray-500", "gray"];
    case "RUNNING":
      return ["bg-dwlightblue/50", "bg-dwlightblue", "rgb(66,157,188, 0.5)"];
    default:
      return ["bg-gray-500/50", "bg-gray-500", "gray"];
  }
};

export const getMinWidth = (minStartTime: number, maxEndTime: number) => {
  const timeRange = maxEndTime - minStartTime;
  const minWidth = timeRange / 200;
  return minWidth;
};

const options = {
  indexAxis: "y" as const,
  legend: {
    display: true,
  },
  layout: {
    autoPadding: false,
  },
  elements: {
    bar: {
      borderWidth: 0,
    },
  },
  scales: {
    y: {
      stacked: true,
      display: false,
      beginAtZero: true,
      // type: "linear" as const,
      barPercentage: 0.9,
      categoryPercentage: 1.0,
      grace: "0%",
    },
    x: {
      stacked: true,
      display: true,
      beginAtZero: true,
      grace: "0%",
      ticks: {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        callback: function (value: any) {
          return value + "s";
        },
      },
    },
  },
  responsive: true,
  maintainAspectRatio: false,
  // resizeDelay: 200,
  plugins: {
    zoom: {
      zoom: {
        wheel: {
          enabled: true,
        },
        pinch: {
          enabled: true,
        },
        mode: "xy" as const,
      },
      pan: {
        enabled: true,
        mode: "xy" as const,
        drag: true,
      },
    },

    tooltip: {
      callbacks: {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        label: function (ctx: any) {
          const [startTime, endTime] = ctx.dataset.data[ctx.dataIndex];
          let difference =
            endTime - startTime - getMinWidth(startTime, endTime);
          if (Math.abs(difference) < 0.001) {
            difference = 0;
          }
          const formattedTime = `${difference.toFixed(3)}s`;
          return formattedTime;
        },
      },
    },
    title: {
      display: true,
    },
    legend: {
      position: "bottom" as const,
      display: false,
    },
    // callbacks: {
    //   labelPointStyle: (context: any) => {
    //     return {
    //       // rotation: 90,
    //     };
    //   },
    // },
  },
};

export const WaterfallChart: React.FC<{
  run: DAGRunWithData;
  highlightedTasks: string[] | null;
  setHighlightedTasks: (tasks: string[] | null) => void;
  isHighlighted: boolean;
  setHighlighted: (highlighted: boolean) => void;
}> = (props) => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const chartRef = useRef<any>(null);
  const handleResetZoom = () => {
    if (chartRef && chartRef.current) {
      chartRef.current.resetZoom();
    }
  };
  const nodesWithValidStartAndEndTimes = props.run.node_runs.filter(
    (n) => n.start_time && n.end_time
  );

  const timeRangesAsSeconds = nodesWithValidStartAndEndTimes
    .map((node) => [
      new Date(node.start_time as string).getTime() / 1000,
      new Date(node.end_time as string).getTime() / 1000,
    ])
    .sort((a, b) => a[0] - b[0]);

  const minStartTime = Math.min(
    ...timeRangesAsSeconds.map((range) => range[0])
  );

  const maxEndTime = Math.max(...timeRangesAsSeconds.map((range) => range[1]));

  const minWidth = getMinWidth(minStartTime, maxEndTime);
  const data = {
    labels: nodesWithValidStartAndEndTimes.map((node) => node.node_name),
    datasets: [
      {
        barPercentage: 0.99,
        categoryPercentage: 1.0,
        fill: true,
        title: "test",
        borderWidth: 0,
        data: timeRangesAsSeconds.map((range) => {
          let start = range[0] - minStartTime;
          let end = range[1] - minStartTime;
          if (end - start < minWidth) {
            start = start - minWidth / 2;
            end = start + minWidth;
          }

          return [start, end];
        }),
        backgroundColor: nodesWithValidStartAndEndTimes.map((node) => {
          const out = getColor(node)[2];
          if (props.highlightedTasks?.includes(node.node_name)) {
            return out.replace("0.5", "1");
          }
          return out;
        }),
        backgroundOpacity: 0.5,
      },
    ],
  };

  return (
    <div
      className={`relative w-full h-500 ${
        props.isHighlighted ? "bg-dwdarkblue/20" : ""
      }`}
    >
      <Bar options={options} ref={chartRef} data={data} height={500} />
      <button
        className="absolute top-2.5 right-2.5 bg-dwlightblue/80 text-white px-4 py-.5 border rounded"
        onClick={handleResetZoom}
      >
        reset
      </button>
    </div>
  );
};

export default WaterfallChart;
