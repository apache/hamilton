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

/**
 * This is legacy code and we will likely stop supporting it.
 * Just kept it around cause one of our customers has old runs on it and I want to test the typing system.
 */
import {
  GenericGroupedTable,
  formatMeanStdDev,
  getMeanStdDev,
} from "../../../../common/GenericTable";
import {
  AttributePandasDescribe1,
  PandasDescribeCategoricalColumn,
  PandasDescribeNumericColumn,
} from "../../../../../state/api/backendApiRaw";
import { RunLink } from "../../../../common/CommonLinks";

export const isPandasDescribeNumericColumn = (
  obj: any // eslint-disable-line @typescript-eslint/no-explicit-any
): obj is PandasDescribeNumericColumn => {
  return [
    "Int8",
    "Int16",
    "Int32",
    "Int64",
    "UInt8",
    "UInt16",
    "UInt32",
    "UInt64",
    "float64",
  ]
    .map((s) => s.toLowerCase())
    .includes(obj.dtype?.toLowerCase());
};

export const isPandasDescribeCategoricalColumn = (
  obj: any // eslint-disable-line @typescript-eslint/no-explicit-any
): obj is PandasDescribeCategoricalColumn => {
  return ["string", "object", "category", "bool"].includes(obj.dtype);
};

type PandasDescribeCategoricalColumnWithMetadata = {
  runId: number;
  projectId: number;
} & PandasDescribeCategoricalColumn;
type PandasDescribeNumericColumnWithMetadata = {
  runId: number;
  projectId: number;
} & PandasDescribeNumericColumn;

export const splitColumnsByObjectType = (
  results: AttributePandasDescribe1[],
  runIds: number[],
  projectId: number
) => {
  const numericColumns: [
    string,
    { runId: number; projectId: number } & PandasDescribeNumericColumn
  ][] = [];
  const categoricalColumns: [
    string,
    { runId: number; projectId: number } & PandasDescribeCategoricalColumn
  ][] = [];

  results.forEach((result, i) => {
    Object.entries(result).forEach(([key, value]) => {
      if (isPandasDescribeNumericColumn(value)) {
        const valueWithMetadata = {
          runId: runIds[i],
          ...value,
          projectId: projectId,
        };
        numericColumns.push([key, valueWithMetadata]);
      } else if (isPandasDescribeCategoricalColumn(value)) {
        const valueWithMetadata = {
          runId: runIds[i],
          ...value,
          projectId: projectId,
        };
        categoricalColumns.push([key, valueWithMetadata]);
      }
    });
  });

  return {
    numericColumns,
    categoricalColumns,
  };
};

const numericColumnRows = [
  {
    displayName: "count",
    Render: (value: PandasDescribeNumericColumn[], isSummaryRow: boolean) => {
      const numericValues = value.map((item) => item.count);
      if (!isSummaryRow) {
        return <div>{numericValues[0].toFixed(2)}</div>;
      }
      const meanStdDev = getMeanStdDev(numericValues);
      return <div>{formatMeanStdDev(meanStdDev.mean, meanStdDev.stdDev)}</div>;
    },
  },
  {
    displayName: "mean",
    Render: (value: PandasDescribeNumericColumn[], isSummaryRow: boolean) => {
      const numericValues = value.map((item) => item.mean);
      if (!isSummaryRow) {
        return <div>{numericValues[0].toFixed(2)}</div>;
      }
      const meanStdDev = getMeanStdDev(numericValues);
      return <div>{formatMeanStdDev(meanStdDev.mean, meanStdDev.stdDev)}</div>;
    },
  },
  {
    displayName: "std",
    Render: (value: PandasDescribeNumericColumn[], isSummaryRow: boolean) => {
      const numericValues = value.map((item) => item.std);
      if (!isSummaryRow) {
        return <div>{numericValues[0].toFixed(2)}</div>;
      }
      const meanStdDev = getMeanStdDev(numericValues);
      return <div>{formatMeanStdDev(meanStdDev.mean, meanStdDev.stdDev)}</div>;
    },
  },
  {
    displayName: "quantiles",
    Render: (value: PandasDescribeNumericColumn[], isSummaryRow: boolean) => {
      if (isSummaryRow) {
        return <></>;
      }
      // This is using a library this is not particularly maintained, but its a quick solution
      // At some point we'll want to figure out a better way to handle this
      //eslint-disable-next-line @typescript-eslint/no-var-requires
      const MicroBarChart = require("react-micro-bar-chart");
      const quantileLabels = ["min", "25%", "50%", "75%", "max"];
      const first = value[0];
      const quantileData = [
        first.min,
        first.q_25_percent,
        first.q_50_percent,
        first.q_75_percent,
        first.max,
      ].map((item) => (item == 0 ? first.max * 0.05 : item));
      return (
        // <></>
        <MicroBarChart
          hoverColor="rgb(66,157,188)"
          fillColor="rgb(43,49,82)"
          tipOffset={[0, 10]}
          tooltip
          // eslint-disable-next-line @typescript-eslint/no-unused-vars, @typescript-eslint/no-explicit-any
          tipTemplate={(d: number, i: number) => {
            return `${quantileLabels[i]}: ${d
              .toFixed(2)
              .replace(/([0-9]+(\.[0-9]+[1-9])?)(\.?0+$)/, "$1")}`;
          }}
          data={quantileData}
        />
      );
    },
  },
  {
    displayName: "Runs",
    Render: (
      value: PandasDescribeNumericColumnWithMetadata[],
      isSummaryRow: boolean,
      isExpanded: boolean
    ) => {
      // This is pretty sloppy but it'll do for now
      // const {projectId} = useProjectGlobals();
      // if (isSummaryRow) {
      //   return <></>;
      // }
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
];

const categoricalColumnRows = [
  {
    displayName: "count",
    Render: (
      value: PandasDescribeCategoricalColumn[],
      isSummaryRow: boolean
    ) => {
      const numericValues = value
        .map((item) => item.count)
        .filter((item) => item !== undefined) as number[];
      if (!isSummaryRow) {
        return <div>{numericValues[0].toFixed(2)}</div>;
      }
      const meanStdDev = getMeanStdDev(numericValues);
      return <div>{formatMeanStdDev(meanStdDev.mean, meanStdDev.stdDev)}</div>;
    },
  },
  {
    displayName: "top",
    Render: (
      value: PandasDescribeCategoricalColumn[],
      isSummaryRow: boolean
    ) => {
      if (!isSummaryRow) {
        return <pre>{value[0].top?.toString() || ""}</pre>;
      }
      return <></>;
    },
  },
  {
    displayName: "freq",
    Render: (
      value: PandasDescribeCategoricalColumn[],
      isSummaryRow: boolean
    ) => {
      if (!isSummaryRow) {
        return (
          <div>
            {value[0].count === undefined || value[0].count === null
              ? ""
              : (((value[0].freq || 0) * 100) / value[0].count).toFixed(2)}
            %
          </div>
        );
      }
    },
  },
  {
    displayName: "unique",
    Render: (value: PandasDescribeCategoricalColumn[], isSummaryRow: boolean) =>
      isSummaryRow ? <></> : <div>{value[0].unique}</div>,
  },
  {
    displayName: "Runs",
    Render: (
      value: PandasDescribeCategoricalColumnWithMetadata[],
      isSummaryRow: boolean,
      isExpanded: boolean
    ) => {
      // This is pretty sloppy but it'll do for now
      // const {projectId} = useProjectGlobals();
      // if (isSummaryRow) {
      //   return <></>;
      // }
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

  // {
  //   displayName: "Runs",
  //   render: (value: {PandasDescribeCategoricalColumn & {runId : number}}[], isSummaryRow: boolean) => {
  //     if (isSummaryRow) {
  //       return <></>;
  //     }
  //     return (
  //       <div className="flex flex-row gap-1">
  //         {props.taskRuns.map((taskRun, i) => (
  //           <Link
  //             className="text-dwlightblue hover:underline"
  //             to={`/dashboard/project/${props.projectId}/runs/${props.runIds[i]}`}
  //             key={i}
  //           >
  //             {props.runIds[i]}
  //           </Link>
  //         ))}
  //       </div>
  //     );
  //   },
  // },
];

export const PandasDescribe1View = (props: {
  taskName: string;
  runIds: number[];
  values: AttributePandasDescribe1[];
  projectId: number;
}) => {
  const resultsSplitByObjectType = splitColumnsByObjectType(
    props.values,
    props.runIds,
    props.projectId
  );
  const { numericColumns, categoricalColumns } = resultsSplitByObjectType;
  return (
    <div>
      {numericColumns.length > 0 ? (
        <div className="py-10">
          <GenericGroupedTable
            dataTypeName="column"
            data={numericColumns}
            name="Numeric Columns"
            // description="Numeric columns in the dataset"
            columns={numericColumnRows}
          />
        </div>
      ) : (
        <></>
      )}
      {categoricalColumns.length > 0 ? (
        <div className="py-10">
          <GenericGroupedTable
            dataTypeName="column"
            data={categoricalColumns}
            name="Categorical Columns"
            // description="Numeric columns in the dataset"
            columns={categoricalColumnRows}
          />
        </div>
      ) : (
        <></>
      )}
    </div>
  );
};
