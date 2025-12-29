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

import { ReactNode, useContext } from "react";
import { HelpVideos, TutorialContext } from "../tutorial/HelpVideo";
import { FaQuestionCircle } from "react-icons/fa";

export const WithHelpIcon = (props: {
  children: ReactNode;
  whichIcon: keyof typeof HelpVideos;
  translate?: string;
}) => {
  const { setLoomVideoOpen, includeHelp, setCurrentLoomVideo } =
    useContext(TutorialContext);
  return (
    <div>
      {includeHelp ? (
        <FaQuestionCircle
          className={`text-yellow-400 text-sm fixed hover:cursor-pointer hover:scale-150 ${
            props.translate || ""
          }`}
          onClick={() => {
            setCurrentLoomVideo(props.whichIcon);
            setLoomVideoOpen(true);
          }}
        />
      ) : null}
      {props.children}
    </div>
  );
};
