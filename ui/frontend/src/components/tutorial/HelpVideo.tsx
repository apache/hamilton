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

// List of help videos
export const HelpVideos = {
  PROJECT_SELECTOR: "d6787ecc66794ad8b3d25023d58e1751", // Referred to in the project selector on the main page
  API_KEYS: "1353ba25f0b4422cbfbb4559bb44760e", // Referred to in the dashboard
  // ACCOUNT: "...", // Referred to in the account section
  VERSIONS: "6bdb9b8b80af41f1bd7de89ac4ddc16a", // Referred to in the version selector section
  STRUCTURE: "ae51932617cb4e4f9b0399e33ad504f9", // Referred to in the structure section
  RUNS: "16c7c5e24c8a4e23b55b436068399e9b", // Referred to in the runs section
};
export const LoomHelpVideo = (props: {
  loomId: string;
  height: string;
  width: string;
}) => {
  return (
    <div className="w-full h-full">
      <iframe
        width={props.width}
        height={props.height}
        src={`https://www.loom.com/embed/${props.loomId}?hide_owner=true&hide_share=true&hide_title=true&hideEmbedTopBar=true`}
        frameBorder="0"
        allowFullScreen
      />
    </div>
  );
};

import { Dialog, Transition } from "@headlessui/react";
import { Fragment, createContext } from "react";

export const TutorialContext = createContext<{
  currentLoomVideo: keyof typeof HelpVideos | undefined;
  setCurrentLoomVideo: (video: keyof typeof HelpVideos) => void;
  open: boolean;
  setLoomVideoOpen: (open: boolean) => void;
  includeHelp: boolean;
}>({
  currentLoomVideo: undefined,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  setCurrentLoomVideo: (video: string) => void 0,
  open: false,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  setLoomVideoOpen: (open: boolean) => void 0,
  includeHelp: true,
});

export const HelpModal = (props: {
  whichLoom: keyof typeof HelpVideos;
  open: boolean;
  setOpen: (open: boolean) => void;
}) => {
  const { open, setOpen } = props;
  return (
    <Transition.Root show={open} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={setOpen}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:p-6">
                <LoomHelpVideo
                  loomId={HelpVideos[props.whichLoom]}
                  height="600px"
                  width="1000px"
                />
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  );
};
