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

import { useLayoutEffect, useRef, useState } from "react";
import { classNames } from "../../../utils";
import { AttributeDocumentationLoom1 } from "../../../state/api/friendlyApi";

const Loom_001View = (props: { documentation: object }) => {
  const documentation = props.documentation as {
    id: string;
  };

  const targetRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useLayoutEffect(() => {
    if (targetRef.current) {
      setDimensions({
        width: targetRef.current.clientWidth,
        height: targetRef.current.clientHeight,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetRef.current]);
  return (
    <div ref={targetRef} className="flex justify-center w-full h-full">
      <iframe
        width={`${dimensions.width}px`}
        height={`${dimensions.height}px`}
        src={`https://www.loom.com/embed/${documentation.id}`}
        // frameBorder="0"
        allowFullScreen
      />
    </div>
  );
};

/**
 * Component to render project documentation
 * TODO -- make this generic so we can render multiple types of documentation, each in a tab
 *
 * @param props
 * @returns
 */
export const ProjectDocumentation = (props: {
  loomDocs: { name: string; value: AttributeDocumentationLoom1 }[];
}) => {
  const tabs = props.loomDocs.map((doc) => doc.name);
  const [currentTabIndex, setCurrentTabIndex] = useState(0);
  const currentTab = tabs[currentTabIndex];
  return (
    <div className="w-[90%]">
      <div className="px-5 m-2">
        <div className="h-min">
          {props.loomDocs.length > 1 && (
            <div className="sm:hidden">
              <label htmlFor="tabs" className="sr-only">
                Select a tab
              </label>

              <select
                id="tabs"
                name="tabs"
                className="block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:border-dwdarkblue focus:outline-none focus:ring-dwdarkblue sm:text-sm cursor-pointer"
                defaultValue={tabs.find((tab, i) => currentTabIndex === i)}
              >
                {tabs.map((tab) => (
                  <option key={tab}>{tab}</option>
                ))}
              </select>
            </div>
          )}

          {props.loomDocs.length > 1 && (
            <div className="hidden sm:block">
              <div className="border-b border-gray-200">
                <nav className="-mb-px flex space-x-8" aria-label="Tabs">
                  {tabs.map((tab, i) => (
                    <a
                      key={tab}
                      onClick={() => setCurrentTabIndex(i)}
                      className={classNames(
                        tab === currentTab
                          ? "border-dwlightblue text-dwlightblue"
                          : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 cursor-pointer",
                        "whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium"
                      )}
                      aria-current={tab === currentTab ? "page" : undefined}
                    >
                      {tab}
                    </a>
                  ))}
                </nav>
              </div>
            </div>
          )}
          <div className="flex flex-col gap-2 w-full h-[50rem] py-10">
            <Loom_001View
              documentation={props.loomDocs[currentTabIndex].value}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
