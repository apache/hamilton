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

import dracula from "prism-react-renderer/themes/dracula";
import Highlight, { defaultProps } from "prism-react-renderer";

type NodeVizConsoleProps = {
  nodes: DAGNode[];
  open: boolean;
  setOpen: (v: boolean) => void;
  dagTemplates: DAGTemplateWithData[];
};

import { Fragment } from "react";
import { Dialog, Transition } from "@headlessui/react";
import { classNames } from "../../../utils";
import { DAGNode } from "./types";
import { DAGTemplateWithData } from "../../../state/api/friendlyApi";

export const NodeVizConsole = (props: NodeVizConsoleProps) => {
  // const [open, setOpen] = useState(true);
  const { open, nodes, setOpen } = props;

  const uniqueCodeMap = nodes.reduce((acc, node) => {
    const group = node.codeArtifact?.name;
    if (group === undefined) {
      return acc;
    }
    if (acc.has(group)) {
      acc.get(group)?.push(node);
    } else {
      acc.set(group, [node]);
    }
    return acc;
  }, new Map<string, DAGNode[]>());

  return (
    <Transition.Root show={open} as={Fragment}>
      <Dialog as="div" className="relative" onClose={setOpen} open={open}>
        <div className="fixed inset-0" />

        <div className="absolute inset-0 overflow-hidden">
          <div className="pointer-events-none fixed inset-y-0 -right-0 flex md:max-w-2xl sm:max-w-xl text-sm">
            <Transition.Child
              as={Fragment}
              enter="transform transition ease-in-out duration-500 sm:duration-700"
              enterFrom="translate-x-full"
              enterTo="translate-x-0"
              leave="transform transition ease-in-out duration-500 sm:duration-700"
              leaveFrom="translate-x-0"
              leaveTo="translate-x-full"
            >
              <Dialog.Panel className="pointer-events-auto max-w-6xl w-full">
                <div className="flex h-full flex-col overflow-y-scroll bg-gray-800/80 py-6 shadow-xl z-5w-full">
                  {Array.from(uniqueCodeMap.entries()).map(([, items]) => {
                    const dagIndices = new Set(
                      items.map((node) => node.dagIndex)
                    );
                    return (
                      <>
                        <div className="px-4 sm:px-6">
                          <div className="flex flex-row gap-2">
                            <div className="text-base font-semibold leading-6 text-white break-words w-full flex-row flex-wrap gap-2">
                              <span className="mr-2">
                                {items[0].codeArtifact?.name as string}
                              </span>
                              {Array.from(dagIndices).map((i) => {
                                return (
                                  <span
                                    key={i}
                                    className={classNames(
                                      "bg-dwdarkblue text-white",
                                      "rounded-md px-3 py-2 w-12 text-sm font-medium mr-1"
                                    )}
                                  >
                                    v. {props.dagTemplates[i].id}
                                  </span>
                                );
                              })}
                            </div>
                          </div>
                        </div>
                        <div className="relative mt-1 flex-1 px-4 sm:px-6 w-full ">
                          <div className="flex flex-wrap gap-1 text-white py-2">
                            {items.map((node, i) => (
                              <span
                                key={i}
                                className="bg-gray-400 rounded-lg p-1 text-xs font-light"
                              >
                                {node.name}
                              </span>
                            ))}
                          </div>
                          <Highlight
                            {...defaultProps}
                            theme={dracula}
                            code={
                              (items[0]?.codeContents as string) ||
                              "---- no code logged ----"
                            }
                            language="python"
                          >
                            {({
                              className,
                              style,
                              tokens,
                              getLineProps,
                              getTokenProps,
                            }) => {
                              const styleToRender = {
                                ...style,
                                backgroundColor: "transparent",
                                "word-break": "break-all",
                                "white-space": "pre-wrap",
                              };
                              className += "";
                              return (
                                <pre
                                  className={className}
                                  style={styleToRender}
                                >
                                  {tokens.map((line, i) => (
                                    // eslint-disable-next-line react/jsx-key
                                    <div {...getLineProps({ line, key: i })}>
                                      {line.map((token, key) => (
                                        // eslint-disable-next-line react/jsx-key
                                        <span
                                          hidden={false}
                                          {...getTokenProps({ token, key })}
                                        />
                                      ))}
                                    </div>
                                  ))}
                                </pre>
                              );
                            }}
                          </Highlight>
                          <div
                            className="flex items-center pt-2"
                            aria-hidden="true"
                          >
                            <div className="w-full border-t border-gray-300" />
                          </div>
                        </div>
                      </>
                    );
                  })}
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  );
};
