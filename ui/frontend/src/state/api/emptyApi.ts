// Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.

import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { RootState } from "../store";

/**
 * Initializes an empty API slice
 * We do this so we can generate it later
 * Unfortunately, this is a total mess due to redux state.
 * What we have to do is await the state value to get to what we want, the token we have.
 * What we really should be doing is using a redux integration...
 *
 * Unfortunately the useEffect hook with dispatch won't invalidate the cache...
 * @param getState
 */
const awaitTokenAvailable = async (getState: () => RootState) => {
  const token = (getState() as RootState).auth.authData;
  if (token === null) {
    setTimeout(() => awaitTokenAvailable(getState), 10);
  }
};

const baseQuery = fetchBaseQuery({
  baseUrl: "/",
  timeout: 10000,
  prepareHeaders: async (headers, { getState }) => {
    const getStateTyped = getState as () => RootState;
    await awaitTokenAvailable(getStateTyped);
    const authData = getStateTyped().auth.authData;
    // @ts-ignore
    const token = authData?.accessToken;
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    } else if (process.env.REACT_APP_AUTH_MODE === "local") {
      headers.set("x-api-user", getStateTyped().auth.localUserName || "");
      headers.set("x-api-key", getStateTyped().auth.localAPIKey || "");
      console.log(headers)
    }
    return headers;
  },
});

export const emptySplitApi = createApi({
  baseQuery: baseQuery,
  endpoints: () => ({}),
  reducerPath: "backendApi",
});
