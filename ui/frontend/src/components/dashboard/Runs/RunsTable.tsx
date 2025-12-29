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

import React, { FC, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { RunStatus } from "./Status";
import ReactSelect from "react-select";
import ReactTimeAgo from "react-time-ago";
import {
  DAGRun,
  DAGTemplateWithoutData,
  RunStatusType,
} from "../../../state/api/friendlyApi";
import { RunLink, VersionLink } from "../../common/CommonLinks";
import { DurationDisplay } from "../../common/Datetime";
import { adjustStatusForDuration } from "../../../utils";
import VisibilitySensor from "react-visibility-sensor";

const MAX_COMPARE_RUNS = 5;

const TableRow: React.FC<{
  run: DAGRun;
  version: DAGTemplateWithoutData | undefined;
  projectId: number;
  setVersion: (version: number) => void;
  cols: {
    display: string | JSX.Element;
    render: (props: RenderProps) => JSX.Element;
  }[];
  toggleIncludeVersionInCompare: (include: boolean) => void;
  includedInCompare: boolean;
}> = (props) => {
  return (
    <tr className="hover:bg-slate-100 h-12">
      <td key={"checkbox"} className="py-2 px-3 text-sm max-w-sm text-gray-500">
        <div className="flex h-6 items-center">
          <input
            id="comments"
            aria-describedby="comments-description"
            name="comments"
            type="checkbox"
            checked={props.includedInCompare}
            onChange={(e) => {
              props.toggleIncludeVersionInCompare(e.target.checked);
            }}
            className="h-4 w-4 rounded border-gray-300 text-dwdarkblue focus:ring-dwdarkblue"
          />
        </div>
      </td>
      {props.cols.map((col, index) => {
        const ToRender = col.render;
        return (
          <td key={index} className="py-2 px-3 text-sm max-w-sm text-gray-500">
            {
              <ToRender
                projectId={props.projectId}
                run={props.run}
                status={props.run.run_status}
                version={props.version}
                setVersion={props.setVersion}
              />
            }
          </td>
        );
      })}
    </tr>
  );
};
type RenderProps = {
  projectId: number;
  run: DAGRun;
  status: string;
  version: DAGTemplateWithoutData | undefined;
  setVersion: (version: number) => void;
};
export const RunsTable: FC<{
  projectId: number;
  runs: DAGRun[];
  projectVersions: DAGTemplateWithoutData[];
  selectedTags: string[];
  // selfFilter?: boolean;
}> = (props) => {
  const { projectId } = props;
  const navigate = useNavigate();
  // const [selectedTags, setSelectedTags] = useState([] as string[]);
  const [tagFilters, setTagFilters] = useState(new Map<string, string[]>());
  const [runsToCompare, setRunsToCompare] = useState([] as number[]);

  const selectedTags = props.selectedTags;

  const BASE_COLS = [
    {
      display: (
        <button
          onClick={() => {
            navigate(
              `/dashboard/project/${projectId}/runs/${runsToCompare.join(",")}`
            );
          }}
          type="button"
          disabled={runsToCompare.length < 1}
          className={`runs-compare rounded bg-dwlightblue px-2 py-1 text-sm font-semibold w-20
            text-white shadow-sm hover:bg-dwlightblue focus-visible:outline
              focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-dwlightblue ${
                runsToCompare.length < 1 ? "opacity-70" : ""
              }`}
        >
          {runsToCompare.length >= 2
            ? "Compare"
            : runsToCompare.length == 1
            ? "View"
            : "Select..."}
        </button>
      ),
      render: (props: RenderProps) => (
        // This is a little awkward -- we need to think through the best way to model this (UUIDs? Or just IDs?)
        <div className="w-12">
          <Link
            to={`/dashboard/project/${props.projectId}/runs/${props.run.id}`}
            className="text-dwlightblue flex flex-row gap-2 items-center hover:scale-110 run-link"
          >
            <RunLink
              projectId={props.projectId}
              runId={props.run.id as number}
              setHighlightedRun={() => void 0}
              highlightedRun={null}
            ></RunLink>
          </Link>
        </div>
      ),
    },
    {
      display: "DAG Version",
      render: (props: RenderProps) => {
        return (
          <div className="">
            <Link
              className="text-dwlightblue cursor-pointer truncate flex gap-2 items-center hover:underline"
              to={`/dashboard/project/${props.projectId}/version/${props.run.dag_template}/visualize`}
              // onClick={
              //   // This is a little sloppy -- we should really be ensuring it isn't undefined...
              //   () => props.setVersion(props.run.project_version as number)
              // }
            >
              <VersionLink
                projectId={props.projectId}
                versionId={props.run.dag_template_id as number}
                nodeName={undefined}
              />
              {props.version?.name ? (
                <span>{`(${props.version?.name})`}</span>
              ) : (
                <></>
              )}
            </Link>
          </div>
        );
      },
    },
    {
      display: "Status",
      render: (props: RenderProps) => {
        const status = adjustStatusForDuration(
          props.run.run_status as RunStatusType,
          props.run.run_start_time || undefined,
          props.run.run_end_time || undefined,
          new Date()
        );
        return <RunStatus status={status as RunStatusType} />;
      },
    },
    {
      display: "Duration",
      render: (props: RenderProps) => {
        return (
          <DurationDisplay
            startTime={props.run.run_start_time || undefined}
            endTime={props.run.run_end_time || undefined}
            currentTime={new Date()}
          />
        );
      },
    },
    //   render: (props: RenderProps) => {
    //     const {
    //       formattedHours,
    //       formattedMinutes,
    //       formattedSeconds,
    //       formattedMilliseconds,
    //     } = durationFormat(
    //       props.run.run_start_time || undefined,
    //       props.run.run_end_time || undefined,
    //       new Date()
    //     );
    //     // const out = `${formattedHours}:${formattedMinutes}:${formattedSeconds}.${formattedMilliseconds}`;
    //     const getTextColor = (durationFormat: string) => {
    //       if (durationFormat === "00") {
    //         return "text-gray-200";
    //       }
    //       return ""; // default to standrd
    //     };
    //     const highlightMilliseconds =
    //       formattedMinutes === "00" && formattedHours === "00";
    //     return (
    //       <div className="font-semibold flex gap-0">
    //         <span className={`${getTextColor(formattedHours)}`}>
    //           {formattedHours}:
    //         </span>
    //         <span className={`${getTextColor(formattedMinutes)}`}>
    //           {formattedMinutes}:
    //         </span>
    //         <span className={`${getTextColor(formattedSeconds)}`}>
    //           {formattedSeconds}
    //         </span>
    //         <span
    //           className={`${
    //             highlightMilliseconds
    //               ? getTextColor(formattedMilliseconds)
    //               : "text-gray-200"
    //           }`}
    //         >
    //           .{formattedMilliseconds}
    //         </span>
    //       </div>
    //     );
    //   },
    // },
    {
      display: "Ran",
      render: (props: RenderProps) => {
        // return <span>{parseTime(props.run.start_time)}</span>;
        if (!props.run.run_start_time) {
          return <></>;
        }
        return <ReactTimeAgo date={new Date(props.run.run_start_time)} />;
      },
    },
    {
      display: "Run by",
      render: (props: RenderProps) => (
        // This is a little awkward -- we need to think through the best way to model this (UUIDs? Or just IDs?)
        <span className="font-semibold">
          {props.run.username_resolved || ""}
        </span>
      ),
    },
  ];
  const projectVersionMap = new Map<number, DAGTemplateWithoutData>();
  props.projectVersions.forEach((version) => {
    projectVersionMap.set(version.id as number, version);
  });
  const possibleTagValues = new Map<string, Set<string>>();
  props.runs.forEach((run) => {
    Object.keys(run.tags || {}).forEach((tag) => {
      if (!possibleTagValues.has(tag)) {
        possibleTagValues.set(tag, new Set());
      }
      const tagKey = tag as keyof typeof run.tags;
      possibleTagValues.get(tag)?.add(run.tags?.[tagKey] || "");
    });
  });
  const filteredRuns = props.runs.filter((run) => {
    if (runsToCompare.indexOf(run.id as number) !== -1) {
      return true;
    }
    const tagMatches = Array.from(tagFilters.entries()).every(([tag, vals]) => {
      const tagKey = tag as keyof typeof run.tags;
      return vals.length === 0 || vals.includes(run.tags?.[tagKey] || ""); // VAlue length is zero if no filter is selected
    });
    return tagMatches;
  });

  const tagCols = Array.from(selectedTags).map((tag) => {
    return {
      display: (
        <ReactSelect
          onChange={(selected) => {
            setTagFilters((prev) => {
              const newMap = new Map(prev);
              newMap.set(
                tag,
                selected.map((opt) => opt.value)
              );
              return newMap;
            });
          }}
          className={"w-48"}
          placeholder={tag}
          isMulti
          options={Array.from(possibleTagValues.get(tag) || []).map((tag) => {
            return { label: tag, value: tag };
          })}
        />
      ),
      render: (props: RenderProps) => {
        const tagKey = tag as keyof typeof props.run.tags;
        return (
          <span className="font-semibold">
            {props.run.tags?.[tagKey] || ""}
          </span>
        );
      },
    };
  });
  const allCols = [...BASE_COLS, ...tagCols];
  return (
    <div className="px-4 sm:px-6 lg:px-8 py-2 max-w-full">
      <div className="flex flex-row gap-5 pr-10">
        {/* {props.selfFilter && (
          <TagSelector setSelectedTags={setSelectedTags} allTags={allTags} />
        )} */}
      </div>
      <div className="mt-3 flex flex-col">
        <div className="-my-2 -mx-4 sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
            <table className="min-w-full divide-y divide-gray-300">
              <thead>
                <tr className="">
                  <th className="py-3.5 pl-3 pr-3 text-left text-lg font-semibold text-gray-900">
                    {/* <TbSortDescending className="hover:scale-125 cursor-pointer" /> */}
                  </th>
                  {allCols.map((col, index) => (
                    <th
                      key={index}
                      scope="col"
                      className="py-3.5 pl-3 pr-3 text-left text-sm font-semibold text-gray-900"
                    >
                      {col.display}
                    </th>
                  ))}
                  {<th className="w-6"></th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {[...filteredRuns]
                  .sort((runA, runB) => {
                    // TODO -- include if we want them "above the fold"
                    // Right now its messy, as they move order when you click on them
                    // We should really use pagination here...
                    // if (tagFilters.size > 0) {
                    //   if (runACompare && !runBCompare) {
                    //     return -1;
                    //   }
                    //   if (runBCompare && !runACompare) {
                    //     return 1;
                    //   }
                    // }
                    return (
                      (runB.run_start_time
                        ? new Date(runB.run_start_time).getTime()
                        : new Date().getTime()) -
                      (runA.run_start_time
                        ? new Date(runA.run_start_time).getTime()
                        : new Date().getTime())
                    );
                  })
                  .map((run, index) => {
                    const runID = run.id as number;
                    return (
                      <VisibilitySensor
                          key={index}
                          offset={{ top: -1000, bottom: -1000 }}
                          partialVisibility={true}
                        >
                      <TableRow
                        projectId={projectId as number}
                        run={run}
                        key={index}
                        version={projectVersionMap.get(
                          run.dag_template_id as number
                        )}
                        cols={allCols}
                        setVersion={(version: number) => {
                          navigate(
                            `/dashboard/project/${projectId}/version/${version}`
                          );
                        }}
                        includedInCompare={runsToCompare.indexOf(runID) > -1}
                        toggleIncludeVersionInCompare={(include) => {
                          if (include) {
                            runsToCompare.push(runID);
                            if (runsToCompare.length > MAX_COMPARE_RUNS) {
                              runsToCompare.shift();
                            }
                          } else {
                            const index = runsToCompare.indexOf(runID, 0);
                            if (index > -1) {
                              runsToCompare.splice(index, 1);
                            }
                          }
                          setRunsToCompare(Array.from(runsToCompare));
                        }}
                      />
                      </VisibilitySensor>
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
