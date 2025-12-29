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

import { Link } from "react-router-dom";

// NOTE The Alerts() page is currently not displayed in the UI
export const Alerts = () => {
  const currentURL = new URL(window.location.href);
  const pathParts = currentURL.pathname.split("/");
  // Remove the last part of the path
  pathParts.pop();
  const modifiedPath = pathParts.join("/") + "/runs";
  return (
    <div className="p-16 text-gray-900 text-center">
      Sorry, this feature is not available to you yet. If you are interested in
      trying it out, please reach out to us - info@dagworks.io! In the
      meanwhile, check out your{" "}
      <Link className="text text-dwlightblue hover:underline" to={modifiedPath}>
        run history{" "}
      </Link>{" "}
      to dive into your executions.
    </div>
  );
};
