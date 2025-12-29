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

import { useContext } from "react";
import { UserContext } from "./Login";
import { ProjectLogInstructions } from "../components/dashboard/Project/ProjectLogInstructions";

export const LocalAccount = () => {
  const localAccount = useContext(UserContext)?.username;
  return (
      <div className="mt-20">
        <h1 className="text-3xl font-bold text-gray-700 pl-5 pb-4">Username: {localAccount}</h1>
        <ProjectLogInstructions
          projectId={undefined}
          username={localAccount || ""}
          canWrite={true}
          hideAPIKey
        ></ProjectLogInstructions>
      </div>
  );
};
