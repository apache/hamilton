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

import React, { useState, createContext } from "react";
import { useLocalStorage } from "../utils/localStorage";
import { HiChevronDown, HiChevronUp } from "react-icons/hi";

type UserContextType = {
  username: string;
  setUsername: (username: string) => void;
  userAPIKey: string | undefined;
};

// Creating a context with a default value and type annotation
export const UserContext = createContext<UserContextType | undefined>(
  undefined
);

export const LocalLoginProvider = (props: { children: React.ReactNode }) => {
  const [localUsername, setLocalUsername] = useState<string>("");
  const [localAPIKey, setLocalAPIKey] = useState<string | undefined>("");
  const [keyInputExpanded, setKeyInputExpanded] = useState(false);

  const [username, setUsername] = useLocalStorage(
    "hamilton-username",
    undefined
  );
  const [apiKey, setApiKey] = useLocalStorage("hamilton-api-key", undefined);
  const [authed, setAuthed] = useLocalStorage("authed", "false");
  if (authed === "true") {
    return (
      <UserContext.Provider
        value={{ username: username || "", setUsername, userAPIKey: apiKey }}
      >
        {props.children}
      </UserContext.Provider>
    );
  }

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    event.stopPropagation();
    if (authed != "true") {
      const results = fetch("/api/v1/phone_home", {
        method: "GET",
        headers: {
          "x-api-key": localAPIKey || "",
          "x-api-user": localUsername || "",
        },
      });
      results.then((response) => {
        if (response.status !== 200) {
          setUsername(undefined);
          setApiKey(undefined);
          setAuthed("false");
          alert("Invalid API key or username. Please try again.");
        } else {
          setAuthed("true");
          setUsername(localUsername); // Store username
          setApiKey(localAPIKey); // Store API key
        }
      });
    }
  };

  const KeyInputExpandIcon = keyInputExpanded ? HiChevronUp : HiChevronDown;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 gap-2">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Welcome to the Hamilton UI!
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="flex flex-row items-center">
            <input
              type="text"
              autoComplete="username"
              name="username"
              value={localUsername}
              onChange={(event) => setLocalUsername(event.target.value)}
              placeholder="Username"
              required
              className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-dwdarkblue focus:border-dwdarkblue focus:z-10 sm:text-sm"
            />
          </div>
          {keyInputExpanded && (
            <input
              type="password"
              autoComplete="api-key"
              name="api-key"
              value={localAPIKey}
              onChange={(event) => {
                setLocalAPIKey(event.target.value);
              }}
              placeholder="API Key (leave blank for local mode)"
              className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-dwdarkblue focus:border-dwdarkblue focus:z-10 sm:text-sm"
            />
          )}
          <button
            type="submit"
            className={`group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-dwdarkblue focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-dwdarkblue z-50`}
          >
            <div className="flex flex-row justify-between w-full items-center">
              <div className="w-max">
                <span>Get started!</span>
              </div>
              <KeyInputExpandIcon
                onClick={(e) => {
                  e.stopPropagation();
                  e.preventDefault()
                  setKeyInputExpanded(!keyInputExpanded);
                }}
                className="h-6 w-6 text-white hover:scale-105"
              ></KeyInputExpandIcon>
            </div>
          </button>
        </form>
      </div>
    </div>
  );
};

export const localLogout = (redirectOnLogin: boolean) => {
  localStorage.removeItem("hamilton-username");
  localStorage.removeItem("hamilton-api-key");
  localStorage.removeItem("authed");
  if (redirectOnLogin) {
    window.location.reload();
  }
};

export default LocalLoginProvider;
