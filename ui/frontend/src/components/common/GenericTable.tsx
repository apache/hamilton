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

import React, { FC } from "react";
import { HiChevronDown, HiChevronUp } from "react-icons/hi";

// TODO -- replace all these JSX functions with FC :/
type GenericTableProps<T> = {
  data: [string, T][];
  name?: string;
  columns: {
    displayName: string | JSX.Element;
    Render: (value: T) => React.ReactNode;
  }[];
  // Any extra data to go below in the row
  // rows are supposed to manage their own state if this needs to come/go
  extraRowData?: {
    Render: FC<{ value: T }>;
    shouldRender: (value: T) => boolean;
  };
  dataTypeName: string;
  comparison?: (a: [string, T], b: [string, T]) => number;
  dataTypeDisplay?: (label: string, data: T) => React.ReactNode | undefined;
};

const TableRow = <T extends object>(props: {
  data: T;
  columns: {
    displayName: string | JSX.Element;
    Render: (value: T) => React.ReactNode;
  }[];
  extraRowData?: {
    Render: FC<{ value: T }>;
    shouldRender: (value: T) => boolean;
  };
  name: string;
  dataTypeDisplay?: (label: string, value: T) => React.ReactNode | undefined;
}) => {
  const [highlighted, setHighlighted] = React.useState(false);
  const labelData = (
    <td
      key={props.name}
      className="py-4 px-3 text-sm font-semibold text-gray-500 w-48"
    >
      {props.dataTypeDisplay
        ? props.dataTypeDisplay(props.name, props.data)
        : props.name}
    </td>
  );
  const out = props.columns.map((column, index) => {
    return (
      <td
        key={index + "_expanded"}
        className="whitespace-nowrap py-4 px-3 text-sm text-gray-500"
      >
        {column.Render(props.data)}
      </td>
    );
  });
  const Render =
    props.extraRowData?.Render !== undefined &&
    props.extraRowData?.shouldRender(props.data)
      ? props.extraRowData.Render
      : undefined;
  return (
    <>
      <tr
        className={`${highlighted ? "bg-slate-100" : ""} h-12`}
        onMouseEnter={() => setHighlighted(true)}
        onMouseLeave={() => setHighlighted(false)}
        key={props.name}
      >
        {[labelData, ...out]}
      </tr>
      {Render !== undefined ? (
        <tr>
          <td colSpan={1000}>{<Render value={props.data}></Render>}</td>
          {/* <td colSpan={1000}>{props.extraRowData.Render(props.data)}</td> */}
        </tr>
      ) : (
        <> </>
      )}
    </>
  );
};
export const GenericTable = <T extends object>(props: GenericTableProps<T>) => {
  const sortedData = props.comparison
    ? props.data.sort(props.comparison)
    : props.data;
  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          {props.name ? (
            <h1 className="text-base font-semibold leading-6 text-gray-900">
              {props.name}
            </h1>
          ) : null}
        </div>
      </div>
      <div className="mt-8 flow-root overflow-clip">
        <div className="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full  align-middle sm:px-6 lg:px-8">
            <table className="min-w-full divide-y divide-gray-300">
              <thead>
                <tr>
                  {
                    <th
                      key={"header"}
                      scope="col"
                      className="py-3.5 pl-3 pr-3 text-left text-sm font-semibold text-gray-900"
                    >
                      {props.dataTypeName}
                    </th>
                  }
                  {props.columns.map((column, index) => {
                    return (
                      <th
                        key={index}
                        scope="col"
                        className="py-3.5 pl-3 pr-3 text-left text-sm font-semibold text-gray-900"
                      >
                        {column.displayName}
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {sortedData.map(([name, data]) => {
                  return (
                    <>
                      <TableRow
                        key={name}
                        data={data}
                        name={name}
                        columns={props.columns}
                        extraRowData={props.extraRowData}
                        dataTypeDisplay={props.dataTypeDisplay}
                      />
                    </>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

type GenericGroupedTableProps<T> = {
  data: [string, T][];
  name?: string;
  columns: {
    displayName: string | JSX.Element;
    Render: (
      value: T[],
      isSummaryRow: boolean,
      isExpanded: boolean,
      index?: number | undefined,
      toggleExpanded?: () => void
    ) => React.ReactNode;
  }[];
  dataTypeName: string;
  comparison?: (a: [string, T], b: [string, T]) => number;
  label?: (props: { value: T }) => JSX.Element;
};

const GroupedTableRow = <T extends object>(props: {
  data: T[];
  columns: {
    displayName: string | JSX.Element;
    // TODO -- make this use props
    Render: (
      value: T[],
      isSummaryRow: boolean,
      isExpanded: boolean,
      index?: number | undefined,
      toggleExpanded?: () => void
    ) => React.ReactNode;
  }[];
  label?: (props: { value: T }) => JSX.Element;
  name: string;
  isSummaryRow?: boolean;
  highlighted?: boolean;
  index?: number | undefined;
}) => {
  const [highlighted, setHighlighted] = React.useState(false);
  const [expanded, setExpanded] = React.useState(false);
  const Icon = expanded ? HiChevronUp : HiChevronDown;
  // This is hacky -- we should not force it into this shape
  const expandable = props.data.length > 1 && props.isSummaryRow;
  const Label = props.label;
  const labelData = (
    <td key={props.name} className="px-3 text-sm font-semibold text-gray-500">
      {props.isSummaryRow ? (
        Label !== undefined ? (
          <Label value={props.data[0]} />
        ) : (
          props.name
        )
      ) : (
        <></>
      )}
    </td>
  );
  const columns = props.columns;
  const out = columns.map((column, index) => {
    return (
      <td
        key={index}
        className="whitespace-nowrap py-4 px-3 text-sm text-gray-500"
        onClick={(e) => {
          if (expandable) {
            setExpanded(!expanded);
          }
          e.stopPropagation();
        }}
      >
        {column.Render(
          props.data,
          expandable as boolean,
          expanded,
          props.index,
          expandable ? () => setExpanded(!expanded) : undefined
        )}
      </td>
    );
  });
  return (
    <>
      <tr
        className={`${
          highlighted || props.highlighted ? "bg-slate-100" : ""
        } h-12 ${expandable ? "cursor-cell" : "cursor-default"}`}
        onMouseEnter={() => {
          setHighlighted(true);
        }}
        onMouseLeave={() => {
          setHighlighted(false);
        }}
        key={props.name}
      >
        <td>
          {expandable ? (
            <div className="h-full align-middle items-center">
              <Icon
                className="hover:scale-125 hover:cursor-pointer text-2xl text-gray-400 mr-1"
                onClick={() => {
                  expandable && setExpanded(!expanded);
                }}
              />
            </div>
          ) : null}
        </td>
        {[labelData, ...out]}
      </tr>
      {expanded
        ? props.data.map((data, index) => (
            <GroupedTableRow
              data={[data]}
              name={props.name}
              columns={props.columns}
              key={index}
              isSummaryRow={false}
              highlighted={highlighted}
              label={props.label}
              index={index}
            />
          ))
        : null}
    </>
  );
};

export const GenericGroupedTable = <T extends object>(
  props: GenericGroupedTableProps<T>
) => {
  const groupedData = new Map<string, T[]>();
  // Grouping table data
  props.data.forEach(([name, data]) => {
    const group = groupedData.get(name);
    if (group) {
      group.push(data);
    } else {
      groupedData.set(name, [data]);
    }
  });

  const sortedDataWithDuplicates = props.comparison
    ? props.data.sort(props.comparison)
    : props.data;

  const sortedDataWithoutDuplicates = [] as [string, T][];
  const seen = new Set<string>();
  sortedDataWithDuplicates.forEach(([name, data]) => {
    if (!seen.has(name)) {
      sortedDataWithoutDuplicates.push([name, data]);
      seen.add(name);
    }
  });

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          {props.name ? (
            <h1 className="text-base font-semibold leading-6 text-gray-900">
              {props.name}
            </h1>
          ) : null}
        </div>
      </div>
      <div className="mt-8 flow-root overflow-clip">
        <div className="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full  align-middle sm:px-6 lg:px-8">
            <table className="min-w-full divide-y divide-gray-300">
              <thead>
                <tr>
                  <th
                    key={"expandIcon"}
                    scope="col"
                    className="py-3.5 pl-3 pr-3 text-left text-sm font-semibold text-gray-900"
                  ></th>
                  {
                    <th
                      key={"header"}
                      scope="col"
                      className="py-3.5 pl-3 pr-3 text-left text-sm font-semibold text-gray-900"
                    >
                      {props.dataTypeName}
                    </th>
                  }
                  {props.columns.map((column, index) => {
                    return (
                      <th
                        key={index}
                        scope="col"
                        className="py-3.5 pl-3 pr-3 text-left text-sm font-semibold text-gray-900"
                      >
                        {column.displayName}
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {sortedDataWithoutDuplicates.map((item) => {
                  const name = item[0];
                  const group = groupedData.get(name);
                  return (
                    <GroupedTableRow
                      key={name}
                      data={group || []}
                      name={name}
                      columns={props.columns}
                      isSummaryRow={true}
                      label={props.label}
                    />
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export const getMeanStdDev = (data: number[]) => {
  const mean = data.reduce((a, b) => a + b, 0) / data.length;
  const stdDev = Math.sqrt(
    data.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / data.length
  );
  return { mean, stdDev };
};

export const formatMeanStdDev = (
  mean: number,
  stdDev: number,
  meanDecimalPoints?: number,
  stdDevDecimalPoints?: number
) => {
  if (meanDecimalPoints === undefined) {
    meanDecimalPoints = 2;
  }
  if (stdDevDecimalPoints === undefined) {
    stdDevDecimalPoints = 2;
  }
  if (stdDev === 0) {
    return `${mean.toFixed(meanDecimalPoints)}`;
  }
  return `${mean.toFixed(meanDecimalPoints)} ± ${stdDev.toFixed(
    stdDevDecimalPoints
  )}`;
};
