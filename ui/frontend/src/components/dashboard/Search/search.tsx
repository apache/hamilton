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

/*
  This example requires Tailwind CSS v3.0+

  This example requires some changes to your config:

  ```
  // tailwind.config.js
  module.exports = {
    // ...
    plugins: [
      // ...
      require('@tailwindcss/forms'),
    ],
  }
  ```
*/
import React, {
  Fragment,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Combobox, Dialog, Transition } from "@headlessui/react";
import { MagnifyingGlassIcon } from "@heroicons/react/20/solid";
import {
  ExclamationTriangleIcon,
  LifebuoyIcon,
} from "@heroicons/react/24/outline";
import { Link, useNavigate } from "react-router-dom";

import Fuse from "fuse.js";
import {
  SearchableItem,
  extractSearchables,
  getSearchableCategories,
} from "./searchables";
import {
  DAGTemplateWithData,
  Project,
  useAllProjects,
  useCatalogView,
  useDAGTemplatesByID,
} from "../../../state/api/friendlyApi";
import { CatalogResponse } from "../../../state/api/backendApiRaw";
import { useURLParams } from "../../../state/urlState";
import { skipToken } from "@reduxjs/toolkit/dist/query";

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(" ");
}

type BaseSearchBarProps = {
  open: boolean;
  setOpen: (open: boolean) => void;
};

type SearchBarProps = BaseSearchBarProps & {
  projectId: number | undefined;
  allProjects: Project[] | undefined;
  currentProjectVersions: DAGTemplateWithData[] | undefined;
  catalogData: CatalogResponse | undefined;
};

export const SearchBarWithData: React.FC<SearchBarProps> = (props) => {
  const [rawQuery, setRawQuery] = useState("");
  // initSearchableState();
  // const projects = useProjects({});
  const navigate = useNavigate();
  const handleKeyPress = useCallback((event: KeyboardEvent) => {
    if (event.metaKey && event.key === "k") {
      props.setOpen(true);
      event.preventDefault();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const searchableCategories = getSearchableCategories();
  // if we haven't selected a project yet, we can't search through anything but the basic windows available
  const searchableItems = extractSearchables(
    props.projectId,
    props.allProjects,
    props.currentProjectVersions,
    props.catalogData
  );

  const fuse = useMemo(
    () =>
      new Fuse(searchableItems, {
        keys: ["searchableText"],
        threshold: 0.3,
      }),
    [searchableItems]
  );

  useEffect(() => {
    // attach the event listener
    document.addEventListener("keydown", handleKeyPress);

    // remove the event listener
    return () => {
      document.removeEventListener("keydown", handleKeyPress);
    };
  }, [handleKeyPress]);

  let query = rawQuery;
  searchableCategories.forEach(({ shortcut }) => {
    query = query.startsWith(shortcut) ? query.slice(1, query.length) : query;
  });
  query = query.trim();
  //   const query = rawQuery.replace(/^[#>]/, "");

  // Current categories are the categories that match the first character of the query or
  // all categories if the query is empty/its first one does not match the current one...
  const matchedCategories = searchableCategories.find(
    (item) => item.shortcut == rawQuery[0]
  );
  const filteredCategories = new Set(
    (matchedCategories ? [matchedCategories] : searchableCategories).map(
      (item) => item.name
    )
  );
  let searchResults = fuse.search(query);

  if (query.trim().length === 0) {
    searchResults = searchableItems.map(
      (item) =>
        ({
          item,
          refIndex: 0,
          score: 0,
        } as Fuse.FuseResult<SearchableItem>)
    );
  }

  const filteredResults = new Map<string, SearchableItem[]>();

  searchResults
    .filter(({ item }) => filteredCategories.has(item.category.name))
    .forEach((result) => {
      const { item } = result;
      const { category } = item;
      if (!filteredResults.has(category.name)) {
        filteredResults.set(category.name, []);
      }
      filteredResults.get(category.name)?.push(item);
    });

  const anyResults = searchResults.length > 0;
  return (
    <Transition.Root
      show={props.open}
      as={Fragment}
      afterLeave={() => setRawQuery("")}
      appear
    >
      <Dialog as="div" className="relative z-50" onClose={props.setOpen}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-500 bg-opacity-25 transition-opacity" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto p-4 sm:p-6 md:p-20">
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0 scale-95"
            enterTo="opacity-100 scale-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100 scale-100"
            leaveTo="opacity-0 scale-95"
          >
            <Dialog.Panel className="mx-auto max-w-xl transform divide-y divide-gray-100 overflow-hidden rounded-xl bg-white shadow-2xl ring-1 ring-black ring-opacity-5 transition-all">
              <Combobox
                onChange={(item: SearchableItem) => {
                  navigate(item.href);
                  props.setOpen(false);
                }}
              >
                <div className="relative">
                  <MagnifyingGlassIcon
                    className="pointer-events-none absolute top-3.5 left-4 h-5 w-5 text-gray-400"
                    aria-hidden="true"
                  />
                  <Combobox.Input
                    className="h-12 w-full border-0 bg-transparent pl-11 pr-4 text-gray-800 placeholder-gray-400 focus:ring-0 sm:text-sm"
                    placeholder="Search..."
                    onChange={(event) => setRawQuery(event.target.value)}
                  />
                </div>

                {anyResults && (
                  <Combobox.Options
                    static
                    className="max-h-80 scroll-py-10 scroll-pb-2 space-y-4 overflow-y-auto p-4 pb-2"
                  >
                    {Array.from(filteredResults.entries()).map(
                      ([category, items], index) => {
                        return (
                          items.length > 0 && (
                            <li key={index}>
                              <h2 className="text-xs font-semibold text-gray-900">
                                {category}
                              </h2>
                              <ul className="-mx-4 mt-2 text-sm text-gray-700">
                                {items.map((item, index) => (
                                  <Link to={item.href} key={index}>
                                    <Combobox.Option
                                      onKeyUp={(event: React.KeyboardEvent) => {
                                        if (event.key === "Enter") {
                                          navigate(item.href);
                                          event.preventDefault();
                                        }
                                      }}
                                      key={`${item.name}-${index}-${category}`}
                                      value={item}
                                      className={({ active }) =>
                                        classNames(
                                          "flex cursor-default select-none items-center px-4 py-2",
                                          active
                                            ? "bg-indigo-600 text-white"
                                            : ""
                                        )
                                      }
                                    >
                                      {({ active }) => (
                                        <>
                                          <item.icon
                                            key={`${index}-icon`}
                                            className={classNames(
                                              "h-6 w-6 flex-none",
                                              active
                                                ? "text-white"
                                                : "text-gray-400"
                                            )}
                                            aria-hidden="true"
                                          />
                                          <span
                                            className="ml-3 flex-auto truncate"
                                            key={`${index}-span`}
                                          >
                                            {item.name}
                                          </span>
                                        </>
                                      )}
                                    </Combobox.Option>
                                  </Link>
                                ))}
                              </ul>
                            </li>
                          )
                        );
                      }
                    )}
                  </Combobox.Options>
                )}
                {rawQuery === "?" && (
                  <div className="py-14 px-6 text-center text-sm sm:px-14">
                    <LifebuoyIcon
                      className="mx-auto h-6 w-6 text-gray-400"
                      aria-hidden="true"
                    />
                    <p className="mt-4 font-semibold text-gray-900">
                      Help with searching
                    </p>
                    <p className="mt-2 text-gray-500">
                      Search across your projects, nodes, functions, and
                      DAGWorks offerings.
                    </p>
                  </div>
                )}

                {query !== "" && rawQuery !== "?" && !anyResults && (
                  <div className="py-14 px-6 text-center text-sm sm:px-14">
                    <ExclamationTriangleIcon
                      className="mx-auto h-6 w-6 text-gray-400"
                      aria-hidden="true"
                    />
                    <p className="mt-4 font-semibold text-gray-900">
                      No results found
                    </p>
                    <p className="mt-2 text-gray-500">
                      We couldn’t find anything with that term. Please try
                      again.
                    </p>
                  </div>
                )}

                <div className="flex flex-wrap items-center bg-gray-50 py-2.5 px-4 text-xs text-gray-700 gap-0.5">
                  <>
                    Type {""}
                    {searchableCategories.map((category, index) => {
                      return (
                        <>
                          <kbd
                            key={index}
                            className={classNames(
                              "mx-0.5 flex h-5 w-5 items-center justify-center rounded border bg-white font-semibold",
                              rawQuery.startsWith(category.shortcut)
                                ? "border-indigo-600 text-indigo-600"
                                : "border-gray-400 text-gray-900"
                            )}
                          >
                            {category.shortcut}
                          </kbd>
                          <span className="inline" key={`${index}-span`}>
                            for {category.name}
                            {", "}
                          </span>
                        </>
                      );
                    })}
                    <kbd
                      className={classNames(
                        "mx-0.5 flex h-5 w-5 items-center justify-center rounded border bg-white font-semibold",
                        rawQuery.startsWith("?")
                          ? "border-indigo-600 text-indigo-600"
                          : "border-gray-400 text-gray-900"
                      )}
                    >
                      {"?"}
                    </kbd>
                    <span className="inline">for help.</span>
                  </>
                </div>
              </Combobox>
            </Dialog.Panel>
          </Transition.Child>
        </div>
      </Dialog>
    </Transition.Root>
  );
};

/**
 * Search bar.
 * Currently this fetches its own data, but we might want to share the data from the project
 * so we don't worry about potential inneficiencies due to caching when loading, especially for the more
 * complex queries of data.
 *
 * TODO -- unify these queries so SearchBar is passed stuff rather than querying it directly...
 * Option 1 (worse, but expedient) -- just unify these functions so we can call them, perhaps in friendlyAPI
 * Option 2 (better) -- pass the data in from the project
 * @param props
 * @returns
 */
export const SearchBar: React.FC<BaseSearchBarProps> = (props) => {
  const { projectId, versionIds } = useURLParams();
  const allProjectsResult = useAllProjects({
    limit: 1000,
    offset: 0,
    attributeTypes: "documentation_loom", // We don't really need this, but I'm keeping it there for caching...
  });

  // Parameters for caching
  const dagTemplateVersions = useDAGTemplatesByID(
    versionIds !== undefined
      ? {
          dagTemplateIds: versionIds.join(","),
        }
      : skipToken
  );

  // Parameters for caching
  const catalogData = useCatalogView(
    projectId !== undefined ? { projectId: projectId, limit: 10000 } : skipToken
  );

  return (
    <SearchBarWithData
      open={props.open}
      setOpen={props.setOpen}
      projectId={projectId}
      allProjects={allProjectsResult.data} // TODO -- surface errors in some way?
      currentProjectVersions={dagTemplateVersions.currentData}
      catalogData={catalogData.data}
    />
  );
};
