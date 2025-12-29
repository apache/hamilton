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

import "chartjs-adapter-date-fns";
import { Bar, Scatter } from "react-chartjs-2";
import Datepicker from "react-tailwindcss-datepicker";

import {
  Chart as ChartJS,
  TimeScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Filler,
  Legend,
} from "chart.js";
import ReactSelect from "react-select";
import { useEffect, useState } from "react";
import { RunsTable } from "./RunsTable";
import { GenericTable } from "../../common/GenericTable";
import { MAX_RUNS_QUERIED } from "./Runs";
import { DashboardItem, MetricDisplay } from "./Dashboarding";
import {
  DAGRun,
  DAGTemplateWithoutData,
  RUN_FAILURE_STATUS,
  RUN_SUCCESS_STATUS,
} from "../../../state/api/friendlyApi";
import { useSearchParams } from "react-router-dom";
import {
  TagSelectorWithValues,
  objToSelectedTags,
  selectedTagsToObj,
} from "../../common/TagSelector";

ChartJS.register(
  BarElement,
  TimeScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Legend
);

function formatDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

export const TagSelector = (props: {
  setSelectedTags: (tags: string[]) => void;
  allTags: Set<string>;
}) => {
  const selectOptions = Array.from(props.allTags).map((tag) => {
    return { value: tag, label: tag };
  });
  return (
    <div className="flex-1">
      <ReactSelect
        onChange={(selected) => {
          props.setSelectedTags(selected.map((s) => s.value));
        }}
        options={selectOptions}
        isMulti
        placeholder={"Filter by tags..."}
      />
    </div>
  );
};

export const StatusSelector = (props: {
  possibleStatuses: Set<string>;
  statuses: Set<string>;
  setStatuses: (statuses: Set<string>) => void;
}) => {
  const selectOptions = Array.from(props.possibleStatuses).map((status) => {
    return { value: status, label: status };
  });
  return (
    <div className="flex-1">
      <ReactSelect
        onChange={(selected) => {
          props.setStatuses(new Set(selected.map((s) => s.value)));
        }}
        options={selectOptions}
        isMulti
        placeholder={"Filter by status..."}
        value={Array.from(props.statuses).map((status) => {
          return { value: status, label: status };
        })}
      />
    </div>
  );
};

export const RunCountChart = (props: { runs: DAGRun[] }) => {
  const options = {
    scales: {
      y: {
        beginAtZero: true,
        stacked: true,
      },
      x: {
        stacked: true,
        type: "time" as const,
        time: {
          tooltipFormat: "MMM dd" as const,
          unit: "day" as const,
        },
      },
    },
    responsive: true,
    // resizeDelay: 200,
    plugins: {
      legend: {
        position: "bottom" as const,
        display: false,
      },
      title: {
        display: true,
        text: "Runs Per Day",
      },
    },
  };

  const countByDate = new Map<
    number,
    { [RUN_FAILURE_STATUS]: number; [RUN_SUCCESS_STATUS]: number }
  >();
  props.runs.forEach((run) => {
    const date = run.run_start_time ? new Date(run.run_start_time) : new Date();
    date.setHours(0, 0, 0, 0);
    if (!countByDate.has(date.getTime())) {
      countByDate.set(date.getTime(), {
        [RUN_FAILURE_STATUS]: 0,
        [RUN_SUCCESS_STATUS]: 0,
      });
    }
    if (run.run_status === RUN_SUCCESS_STATUS) {
      (countByDate.get(date.getTime()) as { [RUN_SUCCESS_STATUS]: number })[
        RUN_SUCCESS_STATUS
      ] += 1;
    }
    if (run.run_status === RUN_FAILURE_STATUS) {
      (countByDate.get(date.getTime()) as { [RUN_FAILURE_STATUS]: number })[
        RUN_FAILURE_STATUS
      ] += 1;
    }
  });
  const labels = Array.from(countByDate.keys()).sort((a, b) => {
    return new Date(a).getTime() - new Date(b).getTime();
  });
  const data = {
    labels: labels.map((item) => formatDate(new Date(item))),
    datasets: [
      {
        fill: true,
        label: "Successes",
        data: labels.map(
          (label) => countByDate.get(label)?.[RUN_SUCCESS_STATUS] || 0
        ),
        backgroundColor: "rgb(34, 197, 94)",
        borderColor: "rgb(34, 197, 94)",
        // stack: "Stack 0",
      },
      {
        fill: true,
        label: "Failures",
        data: labels.map(
          (label) => countByDate.get(label)?.[RUN_FAILURE_STATUS] || 0
        ),
        backgroundColor: "rgb(234, 85, 86)",
        borderColor: "rgb(234, 85, 86)",
        // stack: "Stack 1",
      },
    ],
  };
  return (
    // <div className="relative w-[99%] p-2">
    <>
      <div className="w-1 h-1"></div> <Bar options={options} data={data} />
    </>
    // </div>
  );
};

type Query = {
  selectedTags: Map<string, Set<string>>;
  dateRange: { startDate: Date | null; endDate: Date | null };
  statuses: Set<string>;
};
function serialize(query: Query): URLSearchParams {
  const params = new URLSearchParams();
  // Convert complex state to JSON string

  if (query.selectedTags.size > 0) {
    params.set(
      "selectedTags",
      JSON.stringify(selectedTagsToObj(query.selectedTags))
    );
  }
  if (query.dateRange.startDate) {
    params.set("startDate", query.dateRange.startDate.toISOString());
  }
  if (query.dateRange.endDate) {
    params.set("endDate", query.dateRange.endDate.toISOString());
  }
  if (query.statuses.size > 0) {
    params.set("statuses", JSON.stringify(Array.from(query.statuses)));
  }
  return params;
}

function deserialize(
  searchParams: URLSearchParams,
  minDate: Date | null,
  maxDate: Date | null
): Query {
  const selectedTags = searchParams.get("selectedTags");
  const startDate = searchParams.get("startDate");
  const endDate = searchParams.get("endDate");
  const statuses = searchParams.get("statuses");
  const query: Query = {
    selectedTags: new Map<string, Set<string>>(),
    dateRange: {
      startDate: startDate ? new Date(startDate) : minDate,
      endDate: endDate ? new Date(endDate) : maxDate,
    },
    statuses: new Set<string>(),
  };
  if (selectedTags !== null) {
    query.selectedTags = objToSelectedTags(JSON.parse(selectedTags));
  }
  if (statuses !== null) {
    query.statuses = new Set(JSON.parse(statuses));
  }
  return query;
}

const RunQueryFilters = (props: {
  query: Query;
  setQuery: (query: Query) => void;
  allTagOptions: Map<string, Set<string>>;
  allStatusOptions: Set<string>;
}) => {
  return (
    <div className="flex flex-wrap gap-4 items-center">
      <div className="w-full lg:w-144">
        <TagSelectorWithValues
          selectedTags={props.query.selectedTags}
          setSelectedTags={(selectedTags) => {
            props.setQuery({ ...props.query, selectedTags: selectedTags });
          }}
          allTags={props.allTagOptions}
        />
      </div>
      <div className="flex-grow lg:w-auto">
        <Datepicker
          value={props.query.dateRange}
          onChange={(dateRange) => {
            // TODO -- determine what to do with date range if it is null
            if (dateRange !== null) {
              const { startDate, endDate } = dateRange;
              props.setQuery({
                ...props.query,
                dateRange: {
                  startDate: startDate === null ? null : new Date(startDate),
                  endDate: endDate === null ? null : new Date(endDate),
                },
              });
            }
          }}
          showShortcuts={true}
        />
      </div>
      <div className="flex-grow lg:w-auto">
        <StatusSelector
          possibleStatuses={props.allStatusOptions}
          statuses={props.query.statuses}
          setStatuses={(statuses) => {
            props.setQuery({ ...props.query, statuses: statuses });
          }}
        />
      </div>
    </div>
  );
};

export const extractStatusOptions = (runs: DAGRun[]) => {
  const allStatuses = new Set<string>();
  runs.forEach((run) => {
    allStatuses.add(run.run_status);
  });
  return allStatuses;
};

export const extractTagOptions = (runs: DAGRun[]) => {
  const allTags = new Map<string, Set<string>>();
  runs.forEach((run) => {
    Object.entries(run.tags || {}).forEach(([tag, value]) => {
      if (!allTags.has(tag)) {
        allTags.set(tag, new Set<string>());
      }
      allTags.get(tag)?.add(value);
    });
  });
  return allTags;
};

export const filterOnQuery = (runs: DAGRun[], query: Query) => {
  const out = runs.filter((run) => {
    const createdDate = new Date(run.created_at);
    const { startDate, endDate } = query.dateRange as {
      startDate: Date;
      endDate: Date;
    };
    if (startDate !== null && createdDate.getTime() < startDate.getTime()) {
      return false;
    }
    if (endDate !== null && createdDate.getTime() > endDate.getTime()) {
      return false;
    }
    const runTags = run.tags as { [key: string]: string } | undefined;
    if (runTags !== undefined) {
      let tagsMatch = true;
      query.selectedTags.forEach((values, tag) => {
        // If we don't have the tag as a property, it doesn't count
        if (!Object.prototype.hasOwnProperty.call(runTags, tag)) {
          tagsMatch = false;
        }
        // If we have the tag as a property, but the value is not in the set, it doesn't count
        if (!values.has(runTags[tag])) {
          tagsMatch = false;
        }
      });
      if (!tagsMatch) {
        return false;
      }
    }
    if (query.statuses.size > 0) {
      if (!query.statuses.has(run.run_status)) {
        return false;
      }
    }
    return true;
  });
  return out;
};

export const NumRunsMetric = (props: { runs: DAGRun[] }) => {
  const numRuns = props.runs.length;
  const numFailures = props.runs.filter(
    (run) => run.run_status === RUN_FAILURE_STATUS
  ).length;
  const numSuccesses = props.runs.filter(
    (run) => run.run_status === RUN_SUCCESS_STATUS
  ).length;
  const isSubset = numRuns >= MAX_RUNS_QUERIED;
  return (
    // Lazy flexbox here...
    <div className="flex flex-row justify-center items-center h-full w-full">
      <div className="flex flex-row gap-10 justify-between">
        <MetricDisplay
          isSubset={isSubset}
          number={numRuns}
          label="Runs"
          textColorClass="text-gray-900"
        />
        <MetricDisplay
          isSubset={isSubset}
          number={numSuccesses}
          label="Success"
          textColorClass="text-green-500"
        />
        <MetricDisplay
          isSubset={isSubset}
          number={numFailures}
          label="Failed"
          textColorClass="text-dwred"
        />
      </div>
    </div>
  );
};

export const splitToSuccessesAndFailures = (runs: DAGRun[]) => {
  return {
    successes: runs.filter((run) => run.run_status === RUN_SUCCESS_STATUS),
    failures: runs.filter((run) => run.run_status === RUN_FAILURE_STATUS),
  };
};
export const RunDurationScatter = (props: { runs: DAGRun[] }) => {
  const convertRunsToDuration = (runs: DAGRun[]) => {
    return runs.map((item) => ({
      y:
        ((item.run_end_time
          ? new Date(item.run_end_time).getTime()
          : new Date().getTime()) -
          (item.run_start_time
            ? new Date(item.run_start_time).getTime()
            : new Date().getTime())) /
        1000,
      x: item.run_start_time ? new Date(item.run_start_time) : new Date(),
      label: "hello",
    }));
  };
  const { successes, failures } = splitToSuccessesAndFailures(props.runs);
  const data = {
    datasets: [
      {
        label: "Successes",
        labels: successes.map((item) => item.id),
        data: convertRunsToDuration(successes),
        // TODO -- use classes from tailwind
        backgroundColor: "rgb(34, 197, 94)",
        borderColor: "rgb(34, 197, 94)",
      },
      {
        label: "Failures",
        labels: failures.map((item) => item.id),
        data: convertRunsToDuration(failures),
        backgroundColor: "rgb(234, 85, 86)",
        borderColor: "rgb(234, 85, 86)",
      },
    ],
  };
  const options = {
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: "Run Duration (s)",
      },
      tooltip: {
        callbacks: {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          label: function (ctx: any) {
            const label = ctx.dataset.labels[ctx.dataIndex];
            return `Run: ${label}`;
          },
        },
      },
    },
    scales: {
      x: {
        type: "time" as const,
        time: {
          tooltipFormat: "MMM dd" as const,
          unit: "day" as const,
        },
      },
      y: {
        display: true,
        beginAtZero: true,
        ticks: {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          callback: function (value: any) {
            return value + "s";
          },
        },
      },
    },
  };
  // The weird extra div is to make the chart responsive
  return (
    <>
      <div className="w-1 h-1"></div> <Scatter data={data} options={options} />
    </>
  );
};

// TODO -- ensure this + the previous one share code
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export const RunNumberNodesExecuted = (props: { runs: DAGRun[] }) => {
  return <div>TODO -- get the node count for a run...</div>;
  // const convertRunsToDuration = (runs: DAGRun[]) => {
  //   return runs.map((item) => ({
  //     y: item.nodes_executed || 0, // TODO -- un-ignore when we get it in the backend
  //     x: new Date(item.start_time),
  //   }));
  // };
  // const { successes, failures } = splitToSuccessesAndFailures(props.runs);
  // const data = {
  //   datasets: [
  //     {
  //       label: "Successes",
  //       labels: successes.map((item) => item.id),
  //       data: convertRunsToDuration(successes),
  //       // TODO -- use classes from tailwind
  //       backgroundColor: "rgb(34, 197, 94)",
  //       borderColor: "rgb(34, 197, 94)",
  //     },
  //     {
  //       label: "Failures",
  //       labels: failures.map((item) => item.id),
  //       data: convertRunsToDuration(failures),
  //       backgroundColor: "rgb(234, 85, 86)",
  //       borderColor: "rgb(234, 85, 86)",
  //     },
  //   ],
  // };
  // const options = {
  //   plugins: {
  //     legend: {
  //       display: false,
  //     },
  //     title: {
  //       display: true,
  //       text: "# of nodes executed",
  //     },
  //     tooltip: {
  //       callbacks: {
  //         label: function (ctx: any) {
  //           const label = ctx.dataset.labels[ctx.dataIndex];
  //           return `Run: ${label}`;
  //         },
  //       },
  //     },
  //   },
  //   scales: {
  //     x: {
  //       type: "time" as const,
  //       time: {
  //         tooltipFormat: "MMM dd" as const,
  //         unit: "day" as const,
  //       },
  //     },
  //     y: {
  //       beginAtZero: true,
  //     },
  //   },
  // };
  // // The weird extra div is to make the chart responsive
  // return (
  //   <>
  //     <div className="w-1 h-1"></div> <Scatter data={data} options={options} />
  //   </>
  // );
};

type DAGVersionTableRenderProps = {
  numSuccesses: number;
  numFailures: number;
  meanDuration: number;
};
export const DAGVersionTable = (props: {
  projectVersions: DAGTemplateWithoutData[];
  runs: DAGRun[];
  numVersionsToDisplay: number;
}) => {
  const projectVersionMap = new Map<number, DAGTemplateWithoutData>();
  props.projectVersions.forEach((version) => {
    projectVersionMap.set(version.id as number, version);
  });
  const runsByDAGName = new Map<string, DAGRun[]>();
  props.projectVersions.forEach((version) => {
    runsByDAGName.set(
      version.name,
      (runsByDAGName.get(version.name) || []).concat(
        props.runs.filter((run) => run.dag_template === version.id)
      )
    );
  });
  const topNVersions = Array.from(runsByDAGName.entries())
    .sort((a, b) => b[1].length - a[1].length)
    .slice(0, props.numVersionsToDisplay);

  const tableData = topNVersions.map(
    ([projectVersionName, runs]): [string, DAGVersionTableRenderProps] => {
      return [
        projectVersionName,
        {
          numSuccesses: runs.filter(
            (run) =>
              run.run_status === "SUCCESS" && run.run_end_time !== undefined
          ).length,
          numFailures: runs.filter(
            (run) =>
              run.run_status === "FAILURE" && run.run_start_time !== undefined
          ).length,
          meanDuration:
            runs
              .filter((run) => run.run_end_time)
              .reduce(
                (acc, run) =>
                  acc +
                  (new Date(run.run_end_time as string).getTime() -
                    new Date(run.run_start_time as string).getTime()) /
                    1000,
                0
              ) / runs.length,
        },
      ];
    }
  );

  const cols = [
    {
      displayName: "Successes",
      Render: (props: DAGVersionTableRenderProps) => {
        return (
          <div className="text-green-500 font-semibold">
            {props.numSuccesses > 0 ? props.numSuccesses : "-"}
          </div>
        );
      },
    },
    {
      displayName: "Failures",
      Render: (props: DAGVersionTableRenderProps) => {
        return (
          <div className="text-red-500 font-semibold">
            {props.numFailures > 0 ? props.numFailures : "-"}
          </div>
        );
      },
    },
    {
      displayName: "Mean Duration",
      Render: (props: DAGVersionTableRenderProps) => {
        const timeString = isNaN(props.meanDuration)
          ? "-"
          : props.meanDuration.toFixed(3) + "s";
        return <span className="font-semibold">{timeString}</span>;
      },
    },
  ];
  return (
    <GenericTable
      columns={cols}
      data={tableData}
      dataTypeName="Top DAG Names"
    />
  );
};

export const RunSummary = (props: {
  runs: DAGRun[];
  projectId: number;
  dagTemplates: DAGTemplateWithoutData[];
}) => {
  const runsSortedByStartDate = props.runs
    .map((run) =>
      run.run_start_time ? new Date(run.run_start_time) : new Date(Date.now())
    )
    .sort((a, b) => a.getTime() - b.getTime());
  const minDate =
    runsSortedByStartDate.length > 0
      ? new Date(runsSortedByStartDate[0])
      : null;
  const maxDate =
    runsSortedByStartDate.length > 0
      ? new Date(runsSortedByStartDate[runsSortedByStartDate.length - 1])
      : null;

  // Quick buffer to ensure no runs are missed

  if (minDate !== null) {
    minDate.setDate(minDate.getDate() - 1);
  }
  if (maxDate !== null) {
    maxDate.setDate(maxDate.getDate() + 1);
  }

  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(() =>
    deserialize(searchParams, minDate, maxDate)
  );

  useEffect(() => {
    const newSearchParams = serialize(query);
    setSearchParams(newSearchParams, { replace: true });
  }, [query, setSearchParams]);
  const filteredRuns = filterOnQuery(props.runs, query);
  // const filteredRuns = props.runs
  return (
    <div className="max-w-full pt-10">
      <RunQueryFilters
        query={query}
        setQuery={setQuery}
        allTagOptions={extractTagOptions(props.runs)}
        allStatusOptions={extractStatusOptions(props.runs)}
      />
      <div className="flex flex-wrap">
        <DashboardItem>
          <NumRunsMetric runs={filteredRuns} />
        </DashboardItem>
        <DashboardItem>
          <RunCountChart runs={filteredRuns} />
        </DashboardItem>
        <DashboardItem>
          <RunDurationScatter runs={filteredRuns} />
        </DashboardItem>
        {/* <DashboardItem>
          <RunNumberNodesExecuted runs={filteredRuns} />
        </DashboardItem> */}
        <DashboardItem extraWide>
          <DAGVersionTable
            runs={filteredRuns}
            numVersionsToDisplay={3}
            projectVersions={props.dagTemplates}
          />
        </DashboardItem>
      </div>
      <div className="max-w-full">
        <RunsTable
          runs={filteredRuns}
          projectId={props.projectId}
          projectVersions={props.dagTemplates}
          selectedTags={Array.from(query.selectedTags.keys()).sort()}
        />
      </div>
    </div>
  );
};
