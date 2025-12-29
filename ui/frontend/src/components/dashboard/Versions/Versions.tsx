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

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import ReactSelect from "react-select";

import { classNames } from "../../../utils";
import { Loading } from "../../common/Loading";
import { FiExternalLink } from "react-icons/fi";
import { DeleteButton } from "../../common/DeleteButton";
import { ErrorPage } from "../../common/Error";
import {
  DAGTemplateWithoutData,
  ProjectWithData,
  getCodeVersion,
  useLatestDAGTemplates,
  useUpdateDAGTemplate,
} from "../../../state/api/friendlyApi";

import { CodeVersionGit1 } from "../../../state/api/friendlyApi";
import { DateTimeDisplay } from "../../common/Datetime";
interface VersionsProps {
  project: ProjectWithData;
}

interface RenderProps {
  projectId: number;
  version: DAGTemplateWithoutData;
  selected: boolean;
  navigate: (path: string) => void;
  toggleVersionToCompare: (include: boolean) => void;
  includedInCompare: boolean;
  canEditProject: boolean;
}
const MAX_COMPARE_VERSIONS = 3;

const TableRow = (props: {
  projectId: number;
  version: DAGTemplateWithoutData;
  currentProjectVersionIDs: number[] | undefined;
  colsToDisplay: {
    display: string | JSX.Element;
    render: (props: RenderProps) => JSX.Element;
  }[];
  toggleVersionToCompare: (include: boolean) => void;
  includedInCompare: boolean;
  canEditProject: boolean;
}) => {
  const version = props.version;
  const selected =
    (props.currentProjectVersionIDs || ([] as number[])).indexOf(
      version.id as number
    ) != -1;
  const navigate = useNavigate();
  return (
    <tr
      key={version.id}
      className={classNames(
        "pl-2",
        selected ? "bg-dwlightblue/20" : "hover:bg-gray-100"
      )}
    >
      {props.colsToDisplay.map((col, index) => (
        <td
          key={index}
          className={
            index == 0
              ? "whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6 md:pl-2"
              : "whitespace-nowrap py-4  text-sm text-gray-500"
          }
        >
          <col.render
            navigate={navigate}
            projectId={props.projectId}
            version={version}
            selected={selected}
            toggleVersionToCompare={props.toggleVersionToCompare}
            includedInCompare={props.includedInCompare}
            canEditProject={props.canEditProject}
          />
        </td>
      ))}
    </tr>
  );
};
const Versions = (props: VersionsProps) => {
  const [updateDAGTemplate, updateDAGTemplateResult] = useUpdateDAGTemplate();
  const [selectedTags, setSelectedTags] = useState([] as string[]);
  const [selectedNames, setSelectedNames] = useState([] as string[]);
  const [tagFilters, setTagFilters] = useState(new Map<string, string[]>());
  const [versionsToCompare, setVersionsToCompare] = useState([] as number[]);
  const navigate = useNavigate();

  // Currently this just fetches the latest DAG templates
  // Note we might want to do at least one per code-version -- this would involve adding
  // a new endpoint to the backend to do that type of query
  // For now we'll just query enough so we should be fine
  // TODO -- add pagination in the UI
  // TODO -- allow for filter by code version
  // TODO -- determine a good limit (is 500 too high?)
  const projectVersions = useLatestDAGTemplates({
    projectId: props.project.id as number,
    limit: 200,
  });
  projectVersions.data;
  if (
    projectVersions.isLoading ||
    projectVersions.isUninitialized ||
    projectVersions.isFetching ||
    updateDAGTemplateResult.isLoading
  ) {
    return <Loading />;
  } else if (projectVersions.isError) {
    return <ErrorPage message="Failed to load project versions" />;
  } else if (updateDAGTemplateResult.isError) {
    return <ErrorPage message="Failed to set active on DAG template" />;
  }

  const versions = projectVersions.data;
  const allNames = new Set(versions.map((v) => v.name));

  // TODO -- this is copied from RunsTable. We should be able to use the same code
  // Copying it over for now though
  const cols = [
    {
      display: (
        <div>
          <ReactSelect
            onChange={(selected) => {
              setSelectedNames(selected.map((key) => key.label));
            }}
            className={"max-w-xl w-84"}
            placeholder={"Name..."}
            isMulti
            options={Array.from(allNames).map((name) => {
              return { label: name, value: name };
            })}
          />
        </div>
      ),
      render: (props: RenderProps) => (
        // <FeatureNameDisplay name={props.node.name} type={props.node.returnType} />
        <span>{props.version.name}</span>
      ),
    },
    {
      display: "Code Hash",
      render: (props: RenderProps) => {
        // const versionInfo = parseVersionInfo(
        //   props.version
        // ) as GitVersionInfoSchema1;
        const gitVersion = getCodeVersion<CodeVersionGit1>(
          props.version,
          "CodeVersionGit1"
        );
        if (
          gitVersion === undefined ||
          gitVersion.git_repo.startsWith("Error:")
        ) {
          // TODO -- deide/communicate code hash
          return (
            <div className="w-24">
              <span className="block truncate">
                {<code className="">{props.version.code_hash}</code>}
              </span>
            </div>
          );
        } else {
          const gitBaseRepoLink = gitVersion.git_repo
            .replace("git@", "https://")
            .replace("github.com:", "github.com/")
            .replace(".git", "");
          const dagVersionLink = `${gitBaseRepoLink}/tree/${gitVersion.git_hash}`;
          return (
            <div className="w-24">
              <a
                className="text-dwlightblue hover:underline block truncate"
                href={dagVersionLink}
              >
                {<code className="">{props.version.code_hash}</code>}
              </a>
            </div>
          );
        }
      },
    },
    {
      display: "DAG Hash",
      render: (props: RenderProps) => {
        return (
          <div className="w-24">
            <span className="block truncate">
              {<code className="">{props.version.dag_hash}</code>}
            </span>
          </div>
        );
      },
    },
    {
      display: "Created",
      render: (props: RenderProps) => (
        <DateTimeDisplay datetime={props.version.created_at}></DateTimeDisplay>
      ),
    },
    {
      display: "Repository",
      render: (props: RenderProps) => {
        const versionInfo = getCodeVersion<CodeVersionGit1>(
          props.version,
          "CodeVersionGit1"
        );

        if (
          versionInfo === undefined ||
          versionInfo.git_repo.startsWith("Error:")
        ) {
          return <span className="text-gray-400">N/A</span>;
        }
        const gitBaseRepoLink = versionInfo.git_repo
          .replace("git@", "https://")
          .replace("github.com:", "github.com/")
          .replace(".git", "");

        const gitBaseRepoName = gitBaseRepoLink.replace(
          "https://github.com/",
          ""
        );

        return (
          <a
            href={gitBaseRepoLink}
            className="text-dwlightblue hover:underline"
            target="_blank"
            rel="noreferrer"
          >
            {gitBaseRepoName}
          </a>
        );
      },
    },
    {
      display: "",
      render: (props: RenderProps) => {
        return (
          <DeleteButton
            canDelete={props.canEditProject}
            deleteMe={() => {
              updateDAGTemplate({
                dagTemplateId: props.version.id as number,
                dagTemplateUpdate: { is_active: false },
              }).then(() => {
                projectVersions.refetch();
              });
            }}
            deleteType="Archive"
          />
        );
      },
    },
  ];
  const possibleTagValues = new Map<string, Set<string>>();

  versions.forEach((version) => {
    Object.keys(version.tags || {}).forEach((tag) => {
      if (!possibleTagValues.has(tag)) {
        possibleTagValues.set(tag, new Set());
      }
      const tagKey = tag as keyof typeof version.tags;
      possibleTagValues.get(tag)?.add(version.tags?.[tagKey] || "");
    });
  });

  const allTags = new Set(Array.from(possibleTagValues.keys()));
  const checkboxCols = [
    {
      display: "",
      render: (props: RenderProps) => {
        return (
          <div className="flex h-6 items-center">
            <input
              id="comments"
              aria-describedby="comments-description"
              name="comments"
              type="checkbox"
              checked={props.includedInCompare}
              onChange={(e) => {
                // return;
                props.toggleVersionToCompare(e.target.checked);
              }}
              className="h-4 w-4 rounded border-gray-300 text-dwdarkblue focus:ring-dwdarkblue"
            />
          </div>
        );
      },
    },
    {
      display: "",
      render: (props: RenderProps) => (
        // This is a little awkward -- we need to think through the best way to model this (UUIDs? Or just IDs?)
        <div className="w-12">
          <Link
            to={`/dashboard/project/${props.projectId}/version/${props.version.id}`}
            className="text-dwlightblue flex flex-row gap-2 items-center hover:scale-110 versions-link"
          >
            <span>{props.version.id}</span>
            <FiExternalLink className="" />
          </Link>
        </div>
      ),
    },
  ];

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
          // className={"w-48"}
          placeholder={tag}
          isMulti
          options={Array.from(possibleTagValues.get(tag) || []).map((tag) => {
            return { label: tag, value: tag };
          })}
        />
      ),
      render: (props: RenderProps) => {
        const tagKey = tag as keyof typeof props.version.tags;
        return (
          <span className="font-semibold">
            {props.version.tags?.[tagKey] || ""}
          </span>
        );
      },
    };
  });
  const allCols = [...checkboxCols, ...cols, ...tagCols];
  const selectOptions = Array.from(allTags).map((tag) => {
    return { value: tag, label: tag };
  });
  const filteredVersions = versions.filter((version) => {
    const tagMatches = Array.from(tagFilters.entries()).every(([tag, vals]) => {
      const tagKey = tag as keyof typeof version.tags;
      return vals.length === 0 || vals.includes(version.tags?.[tagKey] || ""); // VAlue length is zero if no filter is selected
    });
    return (
      tagMatches &&
      (selectedNames.length === 0 || selectedNames.includes(version.name))
    );
  });

  return (
    <div className="px-4 sm:px-6 lg:px-8 over pt-10">
      <div className="flex flex-row gap-5 pr-10">
        <ReactSelect
          className="flex-1"
          onChange={(selected) => {
            setSelectedTags(selected.map((s) => s.value));
          }}
          options={selectOptions}
          isMulti
          placeholder={"Select tags to view..."}
        />
        <button
          onClick={() => {
            navigate(
              `/dashboard/project/${
                props.project.id
              }/version/${versionsToCompare.join(",")}`
            );
          }}
          type="button"
          disabled={versionsToCompare.length < 1}
          className={`versions-compare rounded bg-dwlightblue px-2 py-1 text-sm font-semibold
            text-white shadow-sm hover:bg-dwlightblue focus-visible:outline
              focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-dwlightblue w-44 ${
                versionsToCompare.length < 1 ? "opacity-70" : ""
              }`}
        >
          {versionsToCompare.length === 0
            ? `Select...`
            : versionsToCompare.length === 1
            ? `View`
            : `Compare ${versionsToCompare.length} versions`}
        </button>
      </div>
      <div className="mt-8 flex flex-col">
        <div className="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
            <table className="min-w-full divide-y divide-gray-300">
              <thead>
                <tr>
                  {allCols.map((col, i) => (
                    <th
                      scope="col"
                      key={i}
                      className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6 md:pl-2"
                    >
                      {col.display}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredVersions.map((version) => (
                  <TableRow
                    projectId={props.project.id}
                    key={version.id}
                    currentProjectVersionIDs={
                      // projectVersions.data?.map((i) => i.id) as number[]
                      []
                    }
                    version={version}
                    colsToDisplay={allCols}
                    includedInCompare={
                      versionsToCompare.indexOf(version.id as number) > -1
                    }
                    canEditProject={props.project.role === "write" || false}
                    toggleVersionToCompare={(include: boolean) => {
                      if (include) {
                        versionsToCompare.push(version.id as number);
                        if (versionsToCompare.length > MAX_COMPARE_VERSIONS) {
                          versionsToCompare.shift();
                        }
                      } else {
                        const index = versionsToCompare.indexOf(
                          version.id as number,
                          0
                        );
                        if (index > -1) {
                          versionsToCompare.splice(index, 1);
                        }
                      }
                      setVersionsToCompare([...versionsToCompare]);
                    }}
                  ></TableRow>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Versions;
