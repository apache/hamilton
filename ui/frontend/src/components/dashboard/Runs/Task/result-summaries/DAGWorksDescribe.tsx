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

import {
  formatMeanStdDev,
  getMeanStdDev,
  GenericGroupedTable,
} from "../../../../common/GenericTable";
import { Bar } from "react-chartjs-2";
import { useLayoutEffect, useRef, useState } from "react";
import { truncateAndRemoveTrailingZeroes } from "../../../../../utils";
import {
  AttributeDagworksDescribe3,
  DwDescribeV003BooleanColumnStatistics,
  DwDescribeV003CategoryColumnStatistics,
  DwDescribeV003NumericColumnStatistics,
  DwDescribeV003StringColumnStatistics,
} from "../../../../../state/api/backendApiRaw";
import { RunLink } from "../../../../common/CommonLinks";


ChartJS.register(
  BarElement,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Legend
);


type DAGWorksDescribe3Base = {
  name: string;
  pos: number;
  data_type: string;
  count: number;
  missing: number;
  base_data_type: string;
};

export const Histogram = (props: {
  histograms: { [range: string]: number }[];
  runIds: number[];
  // Index tells us where this is in the row
  // TODO -- replace with color/some indicator
  index?: number | undefined;
  datatype?: "number" | "datetime";
}) => {
  const datatype = props.datatype || "number";
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const targetRef = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    if (targetRef.current) {
      setDimensions({
        width: targetRef.current.getBoundingClientRect().width,
        height: targetRef.current.getBoundingClientRect().height,
      });
    }
  }, [targetRef]);

  const parser =
    datatype === "datetime" ? (d: string) => new Date(d).getTime() : parseFloat;

  const data = props.histograms.map((histogram, i) => {
    let histogramData = Array.from(Object.entries(histogram)).map(
      ([range, count]) => {
        const [start, end] = range
          .replace("(", "")
          .replace("]", "")
          .replace("]", "")
          .replace("(", "")
          .split(",")
          .map((item) => parser(item));

        const labelProcessed =
          datatype === "number"
            ? range
            : range[0] +
              // TODO -- get the z-value to work so we don't have to truncate too much
              new Date(start).toISOString().split("T")[0] +
              "," +
              new Date(start).toISOString().split("T")[0] +
              range[range.length - 1]; // Remove the decimal points in the time cause we don't need nanos
        return {
          rangeStart: start,
          rangeEnd: end,
          count: count,
          originalLabel: range,
          labelProcessed: labelProcessed,
        };
      }
    );
    histogramData = histogramData.sort((a, b) => a.rangeStart - b.rangeStart);

    // If index is undefined, then we are not in a grouped row
    const index = props.index === undefined ? i : props.index;

    return {
      rangeStart: Math.min(...histogramData.map((item) => item.rangeStart)),
      rangeEnd: Math.max(...histogramData.map((item) => item.rangeEnd)),
      rawData: histogramData,
      datasets: [
        {
          fill: true,
          label: props.runIds[i].toString(),
          labels: histogramData.map((item) => item.rangeStart),
          data: histogramData.map((item) => item.count),
          borderColor: index % 2 === 1 ? "rgb(234, 85, 86)" : "rgb(43,49,82)",
          backgroundColor:
            index % 2 === 1 ? "rgb(234, 85, 86)" : "rgb(43,49,82)",
          barPercentage: 1.0,
          categoryPercentage: 1.0,
        },
      ],
      labels: histogramData.map((item) => item.rangeStart),
    };
  });

  if (data.length > 2) {
    return <span>...</span>;
  }
  const options = (i: number) => {
    return {
      legend: {
        display: false,
      },
      layout: {
        autoPadding: false,
      },
      scales: {
        y: {
          // beginAtZero: true,
          stacked: true,
          display: false,
        },
        x: {
          stacked: true,
          display: false,
          type: "linear" as const,

          categoryPercentage: 1.0,
          barPercentage: 1.0,
          min: data[i].rangeStart,
          max: data[i].rangeEnd,

          // type: "time" as const,
          // time: {
          //   tooltipFormat: "MMM dd" as const,
          //   unit: "day" as const,
          // },
        },
      },
      responsive: true,
      maintainAspectRatio: false,
      // resizeDelay: 200,
      plugins: {
        tooltip: {
          callbacks: {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            title: (context: any) => {
              const index: number = context[0].dataIndex - 1;
              const { labelProcessed, count } = data[i].rawData[index];
              return `${labelProcessed}: ${truncateAndRemoveTrailingZeroes(
                count,
                3
              )}`;
            },
          },
        },
        title: {
          display: false,
        },
        legend: {
          position: "bottom" as const,
          display: false,
        },
        callbacks: {
          labelPointStyle: () => {
            return {
              // rotation: 90,
            };
          },
        },
      },
    };
  };

  return (
    <div className="flex flex-col gap-2">
      {data.map((data, i) => {
        return (
          <>
            <div ref={targetRef} className={`w-[250px] h-[25px]`}>
              <Bar
                options={options(i)}
                height={`${dimensions.height}px`}
                width={`${dimensions.width}px`}
                data={data}
              />
            </div>
          </>
        );
      })}
    </div>
  );
};

export const Quantiles = (props: {
  quantiles: { [range: string]: number | Date }[];
  runIds: number[];
  index: number | undefined;
  datatype: "number" | "datetime";
}) => {
  const datatype = props.datatype;
  const data = props.quantiles.map((histogram, i) => {
    let quantileData = Array.from(Object.entries(histogram)).map(
      ([percentileRaw, value]) => {
        const percentile = parseFloat(percentileRaw);
        return {
          percentile: percentile,
          value: value,
        };
      }
    );
    quantileData = quantileData.sort((a, b) => a.percentile - b.percentile);

    // If index is undefined, then we are not in a grouped row
    const index = props.index === undefined ? i : props.index;
    const range = Array.from(Array(100).keys()).map((i) => i / 100);
    if (quantileData.length === 0) {
      return {
        rawData: [],
        rangeStart: 0,
        rangeEnd: 1,
        dataExpanded: [],
        datasets: [],
        labels: [],
      };
    }
    const minValue = quantileData[0].value;
    const dataExpanded = range.map((fineGrainedPercentile) => {
      const lowestPercentileAbove = quantileData.find(
        (item) => item.percentile >= fineGrainedPercentile
      );
      return lowestPercentileAbove !== undefined
        ? {
            value: lowestPercentileAbove.value,
            percentile: fineGrainedPercentile,
            originalPercentile: lowestPercentileAbove.percentile,
          }
        : { value: minValue, percentile: 0, originalPercentile: 0 };
    });

    return {
      rawData: dataExpanded,
      rangeStart: 0,
      rangeEnd: 1,
      dataExpanded: dataExpanded,
      datasets: [
        {
          fill: true,
          label: props.runIds[i].toString(),
          labels: dataExpanded.map((item) => item.percentile),
          data: dataExpanded.map((item) => {
            return datatype === "datetime"
              ? new Date(item.value).getTime()
              : item.value;
          }),
          borderColor: index % 2 === 1 ? "rgb(234, 85, 86)" : "rgb(43,49,82)",
          backgroundColor:
            index % 2 === 1 ? "rgb(234, 85, 86)" : "rgb(43,49,82)",
          barPercentage: 1.0,
          categoryPercentage: 1.0,
        },
      ],
      labels: dataExpanded.map((item) => item.percentile),
    };
  });

  const toNumber =
    datatype === "datetime"
      ? (d: Date | number) => new Date(d as Date).getTime()
      : (i: number | Date) => i as number;

  if (data.length > 2) {
    return <span>...</span>;
  }
  const options = (i: number) => {
    return {
      legend: {
        display: false,
      },
      layout: {
        autoPadding: false,
      },
      scales: {
        y: {
          min: Math.min(
            // TODO -- fix typing here
            ...data[i].dataExpanded.map((item) => toNumber(item.value))
          ),
          stacked: true,
          display: false,
        },
        x: {
          stacked: true,
          display: false,
          type: "linear" as const,

          categoryPercentage: 1.0,
          barPercentage: 1.0,
          min: Math.min(...data.map((item) => item.rangeStart)),
          max: Math.max(...data.map((item) => item.rangeEnd)),

          // type: "time" as const,
          // time: {
          //   tooltipFormat: "MMM dd" as const,
          //   unit: "day" as const,
          // },
        },
      },
      responsive: true,
      maintainAspectRatio: true,
      // resizeDelay: 200,
      plugins: {
        title: {
          display: false,
        },
        legend: {
          position: "bottom" as const,
          display: false,
        },
        tooltip: {
          callbacks: {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            title: (context: any) => {
              const index: number = context[0].dataIndex - 1;
              const percentile = data[i].rawData[index].originalPercentile;
              const value = data[i].rawData[index].value;
              const valueRepresentation =
                // Typing here is a bit of a mess
                datatype === "datetime"
                  ? new Date(value).toISOString().split(".")[0]
                  : truncateAndRemoveTrailingZeroes(value as number, 3);
              return `${(percentile || 0) * 100}%: ${valueRepresentation}`;
            },
          },
        },
      },
    };
  };

  return (
    <div className="flex flex-col gap-2">
      {data.map((data, i) => {
        return (
          <>
            <div
              // className={`w-full h-[25px] ${i % 2 === 1 ? "-scale-y-100" : ""}`}
              className={`w-[250px] h-[25px]`}
            >
              <div className="h-1 w-1"></div>
              <Bar
                options={options(i)}
                height="30px"
                width="250px"
                data={data}
              />
            </div>
          </>
        );
      })}
    </div>
  );
};

export const splitColumnsByObjectType = (
  results: AttributeDagworksDescribe3[],
  runIds: number[],
  projectId: number
) => {
  const columnsByBaseDataType: {
    [key: string]: [
      string,
      {
        runId: number;
        projectId: number;
      }
    ][];
  } = {
    numeric: [],
    category: [],
    boolean: [],
    datetime: [],
    str: [],
    unhandled: [],
  };

  results.forEach((result, i) => {
    Object.entries(result).forEach(([key, value]) => {
      columnsByBaseDataType[value.base_data_type].push([
        key,
        {
          runId: runIds[i],
          projectId: projectId,
          ...value,
        },
      ]);
    });
  });
  return columnsByBaseDataType;
};

/**
 * Upgraded version of the pandas describe table
 * @param props
 * @returns
 */
export const DAGWorksDescribe3View = (props: {
  taskName: string;
  runIds: number[];
  values: AttributeDagworksDescribe3[];
  projectId: number;
}) => {
  const baseColumns = [
    {
      displayName: "runs",
      Render: (
        value: { runId: number }[],
        isSummaryRow: boolean,
        isExpanded: boolean
      ) => {
        const runIds = value.map((item) => item.runId);
        if (isSummaryRow && isExpanded) {
          return <></>;
        }
        return (
          <div className="flex flex-row gap-1">
            {runIds.map((taskRun, i) => (
              <RunLink
                runId={runIds[i]}
                key={i}
                projectId={1}
                highlightedRun={null}
                setHighlightedRun={() => void 0}
              />
            ))}
          </div>
        );
      },
    },
    {
      displayName: "type",
      Render: (
        value: DAGWorksDescribe3Base[],
        isSummaryRow: boolean,
        isExpanded: boolean
      ) => {
        const toDisplay = Array.from(
          new Set(value.map((item) => item.data_type))
        );
        return !isSummaryRow || !isExpanded ? (
          <div className="flex flex-wrap gap-2">
            {toDisplay.map((item, i) => (
              <code key={i}>{item}</code>
            ))}
          </div>
        ) : (
          <></>
        );
      },
    },
    {
      displayName: "count",
      Render: (
        value: DAGWorksDescribe3Base[],
        isSummaryRow: boolean,
        isExpanded: boolean
      ) => {
        const numericValues = value
          .map((item) => item.count)
          .filter((item) => item !== undefined) as number[];
        if (!isSummaryRow) {
          return <div>{numericValues[0].toFixed(0)}</div>;
        }
        if (isExpanded && numericValues.length > 1) {
          return <></>;
        }
        const meanStdDev = getMeanStdDev(numericValues);
        return (
          <div>
            {formatMeanStdDev(meanStdDev.mean, meanStdDev.stdDev, 0, 0)}
          </div>
        );
      },
    },
    {
      displayName: "missing",
      Render: (
        value: DAGWorksDescribe3Base[],
        isSummaryRow: boolean,
        isExpanded: boolean
      ) => {
        const numericValues = value
          .map((item) => item.missing)
          .filter((item) => item !== undefined) as number[];
        if (!isSummaryRow) {
          if (numericValues[0] === 0) {
            return <div className="text-gray-400"> - </div>;
          }
          return <div>{numericValues[0].toFixed(0)}</div>;
        }
        if (isExpanded && numericValues.length > 1) {
          return <></>;
        }
        const meanStdDev = getMeanStdDev(numericValues);
        if (meanStdDev.mean === 0) {
          return <div className="text-gray-400"> - </div>;
        }
        return (
          <div>{formatMeanStdDev(meanStdDev.mean, meanStdDev.stdDev)}</div>
        );
      },
    },
  ];

  const booleanColumns = [
    ...baseColumns,
    {
      displayName: <code>true</code>,
      Render: (
        value: (DwDescribeV003BooleanColumnStatistics & { runId: number })[],
        isSummaryRow: boolean,
        isExpanded: boolean
      ) => {
        const numericValues = value
          .map((item) => item.zeros)
          .filter((item) => item !== undefined) as number[];
        if (!isSummaryRow) {
          return <div>{numericValues[0]}</div>;
        }
        if (isExpanded && numericValues.length > 1) {
          return <></>;
        }
        const meanStdDev = getMeanStdDev(numericValues);
        if (meanStdDev.mean === 0) {
          return <div className="text-gray-400"> - </div>;
        }
        return (
          <div>
            {formatMeanStdDev(meanStdDev.mean, meanStdDev.stdDev, 0, 0)}
          </div>
        );
      },
    },
    {
      displayName: <code>false</code>,
      Render: (
        value: (DwDescribeV003BooleanColumnStatistics & { runId: number })[],
        isSummaryRow: boolean,
        isExpanded: boolean
      ) => {
        const numericValues = value
          .map((item) => item.count - item.zeros)
          .filter((item) => item !== undefined) as number[];

        if (!isSummaryRow) {
          return <div>{numericValues[0]}</div>;
        }
        if (isExpanded && numericValues.length > 1) {
          return <></>;
        }
        const meanStdDev = getMeanStdDev(numericValues);
        if (meanStdDev.mean === 0) {
          return <div className="text-gray-400"> - </div>;
        }
        return (
          <div>
            {formatMeanStdDev(meanStdDev.mean, meanStdDev.stdDev, 0, 0)}
          </div>
        );
      },
    },
  ];

  const categoricalColumns = [
    ...baseColumns,
    {
      displayName: "unique",
      Render: (
        value: (DwDescribeV003CategoryColumnStatistics & {
          runId: number;
        })[]
      ) => {
        //eslint-disable-next-line no-debugger
        if (value.length > 1) {
          return <></>;
        }
        const numericValue = value[0].unique;
        return <div>{numericValue}</div>;
      },
    },
    {
      displayName: "top value",
      Render: (
        value: (DwDescribeV003CategoryColumnStatistics & {
          runId: number;
        })[]
      ) => {
        //eslint-disable-next-line no-debugger
        if (value.length > 1) {
          return <></>;
        }
        const topItem = value[0].top_value;
        const topCount = value[0].top_freq;
        return (
          <div className="flex flex-row gap-1 items-center">
            {topItem}
            <code>({topCount})</code>
          </div>
        );
      },
    },
  ];

  const numericColumns = [
    ...baseColumns,
    {
      displayName: "mean ± std",
      Render: (
        value: (DwDescribeV003NumericColumnStatistics & { runId: number })[]
      ) => {
        if (value.length > 1) {
          return <></>;
        }
        const meanStr = value[0].mean?.toFixed(2);
        const stdStr = value[0].std?.toFixed(2);

        return (
          <div className="flex flex-row gap-1 items-center">
            <code>
              {meanStr === undefined || stdStr === undefined
                ? ""
                : `${meanStr}±${stdStr}`}
            </code>
          </div>
        );
      },
    },
    {
      displayName: "range",
      Render: (
        value: (DwDescribeV003NumericColumnStatistics & { runId: number })[],
        isSummaryRow: boolean,
        isExpanded: boolean
      ) => {
        const minValue = Math.min(...value.map((item) => item.min));
        const maxValue = Math.max(...value.map((item) => item.max));
        if (isSummaryRow && isExpanded) {
          return <></>;
        }
        return (
          <code>
            [{truncateAndRemoveTrailingZeroes(minValue, 3)},{" "}
            {truncateAndRemoveTrailingZeroes(maxValue, 3)}]
          </code>
        );
      },
    },
    {
      displayName: <code>histogram</code>,
      Render: (
        value: (DwDescribeV003NumericColumnStatistics & { runId: number })[],
        isSummaryRow: boolean,
        isExpanded: boolean,
        index: number | undefined
      ) => {
        const histograms = value.map((item) => item.histogram);
        if (isSummaryRow && isExpanded) {
          return <></>;
        }
        return (
          <div className="w-full h-full">
            <Histogram
              histograms={histograms}
              runIds={props.runIds}
              index={index}
            />
          </div>
        );
      },
    },
    {
      displayName: <code>quantiles</code>,
      Render: (
        value: (DwDescribeV003NumericColumnStatistics & { runId: number })[],
        isSummaryRow: boolean,
        isExpanded: boolean,
        index: number | undefined
      ) => {
        const quantiles = value.map((item) => item.quantiles);
        if (isSummaryRow && isExpanded) {
          return <></>;
        }
        return (
          <Quantiles
            quantiles={quantiles}
            index={index}
            runIds={props.runIds}
            datatype="number"
          />
        );
      },
    },
  ];

  const datetimeColumns = [
    ...baseColumns,
    {
      displayName: "range",
      Render: (
        value: (DwDescribeV003NumericColumnStatistics & { runId: number })[],
        isSummaryRow: boolean,
        isExpanded: boolean
      ) => {
        const minValue = value
          .map((item) => new Date(item.min))
          .sort((a, b) => b.getTime() - a.getTime())[0];
        const maxValue = value
          .map((item) => new Date(item.max))
          .sort((a, b) => b.getTime() - a.getTime())[0];
        if (isSummaryRow && isExpanded) {
          return <></>;
        }
        return (
          <code>
            [{minValue.toDateString()}, {maxValue.toDateString()}]
          </code>
        );
      },
    },
    {
      displayName: <code>histogram</code>,
      Render: (
        value: (DwDescribeV003NumericColumnStatistics & { runId: number })[],
        isSummaryRow: boolean,
        isExpanded: boolean,
        index: number | undefined
      ) => {
        const histograms = value.map((item) => item.histogram);
        if (isSummaryRow && isExpanded) {
          return <></>;
        }
        return (
          <div className="w-full h-full">
            <Histogram
              histograms={histograms}
              runIds={props.runIds}
              index={index}
              datatype="datetime"
            />
          </div>
        );
      },
    },
    {
      displayName: <code>quantiles</code>,
      Render: (
        value: (DwDescribeV003NumericColumnStatistics & { runId: number })[],
        isSummaryRow: boolean,
        isExpanded: boolean,
        index: number | undefined
      ) => {
        const quantiles = value.map((item) => item.quantiles);
        if (isSummaryRow && isExpanded) {
          return <></>;
        }
        return (
          <Quantiles
            quantiles={quantiles}
            index={index}
            runIds={props.runIds}
            datatype="datetime"
          />
        );
      },
    },
  ];

  const stringColumns = [
    ...baseColumns,
    {
      displayName: "mean length",
      Render: (
        value: (DwDescribeV003StringColumnStatistics & {
          runId: number;
        })[]
      ) => {
        //eslint-disable-next-line no-debugger
        if (value.length > 1) {
          return <></>;
        }
        const numericValue = value[0].avg_str_len;
        return <div>{numericValue}</div>;
      },
    },
    {
      displayName: "std length",
      Render: (
        value: (DwDescribeV003StringColumnStatistics & {
          runId: number;
        })[]
      ) => {
        //eslint-disable-next-line no-debugger
        if (value.length > 1) {
          return <></>;
        }
        const numericValue = value[0].std_str_len;
        return <div>{numericValue}</div>;
      },
    },
  ];

  const columnsGroupedByBaseDataType = splitColumnsByObjectType(
    props.values,
    props.runIds,
    props.projectId
  );

  const {
    numeric,
    category,
    boolean,
    datetime,
    str,
    unhandled: unhandledRaw,
  } = columnsGroupedByBaseDataType;

  const unhandledColumns = baseColumns;

  return (
    <div>
      {numeric.length > 0 ? (
        <div className="py-10">
          <GenericGroupedTable
            dataTypeName="column"
            data={
              numeric as [
                string,
                {
                  runId: number;
                  projectId: number;
                } & DwDescribeV003NumericColumnStatistics
              ][]
            }
            name="Numeric Columns"
            // description="Numeric columns in the dataset"
            columns={numericColumns}
          />
        </div>
      ) : (
        <></>
      )}
      {category.length > 0 ? (
        <div className="py-10">
          <GenericGroupedTable
            dataTypeName="column"
            data={
              category as [
                string,
                {
                  runId: number;
                  projectId: number;
                } & DwDescribeV003CategoryColumnStatistics
              ][]
            }
            name="Categorical Columns"
            // description="Categorical columns in the dataset"
            columns={categoricalColumns}
          />
        </div>
      ) : (
        <></>
      )}

      {boolean.length > 0 ? (
        <div className="py-10">
          <GenericGroupedTable
            dataTypeName="column"
            data={
              boolean as [
                string,
                {
                  runId: number;
                  projectId: number;
                } & DwDescribeV003BooleanColumnStatistics
              ][]
            }
            name="Boolean Columns"
            // description="Boolean columns in the dataset"
            columns={booleanColumns}
          />
        </div>
      ) : (
        <></>
      )}

      {datetime.length > 0 ? (
        <div className="py-10">
          <GenericGroupedTable
            dataTypeName="column"
            name="Datetime Columns"
            // description="Datetime columns in the dataset"
            data={
              datetime as [
                string,
                {
                  runId: number;
                  projectId: number;
                } & DwDescribeV003NumericColumnStatistics
              ][]
            }
            columns={datetimeColumns}
          />
        </div>
      ) : (
        <></>
      )}

      {str.length > 0 ? (
        <div className="py-10">
          <GenericGroupedTable
            dataTypeName="column"
            data={
              str as [
                string,
                {
                  runId: number;
                  projectId: number;
                } & DwDescribeV003StringColumnStatistics
              ][]
            }
            name="String Columns"
            // description="String columns in the dataset"
            columns={stringColumns}
          />
        </div>
      ) : (
        <></>
      )}

      {unhandledRaw.length > 0 ? (
        <div className="py-10">
          <GenericGroupedTable
            dataTypeName="column"
            data={
              unhandledRaw as [
                string,
                {
                  runId: number;
                  projectId: number;
                } & DwDescribeV003NumericColumnStatistics
              ][]
            }
            name="Untyped Columns"
            // description="Unhandled columns in the dataset"
            columns={unhandledColumns}
          />
        </div>
      ) : (
        <></>
      )}
    </div>
    // TODO -- add the rest of the columns here with the same pattern as "numeric" above
  );

  return <></>;
};
