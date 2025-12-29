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

import React from "react";

import { ApiKeyOut } from "../../../state/api/backendApiRaw";
import { useAuthData } from "../../../state/authSlice";
import { useAppSelector } from "../../../state/hooks";
import { GenericTable } from "../../common/GenericTable";
import { Loading } from "../../common/Loading";

import { PlusIcon } from "@heroicons/react/24/outline";

import { Fragment, useRef, useState } from "react";
import { Dialog, Transition } from "@headlessui/react";
import { ExclamationTriangleIcon } from "@heroicons/react/24/outline";
import { CheckIcon } from "@heroicons/react/24/outline";
import { FaCopy } from "react-icons/fa";
import { DeleteButton } from "../../common/DeleteButton";
import {
  useAPIKeysFromUser,
  useCreateAPIKey,
  useDeleteAPIKey,
} from "../../../state/api/friendlyApi";


const DEFAULT_API_KEY_NAME = (user: string) => `DAGWorks API Key: ${user}`;

const DeleteAPIKey = (props: {
  open: boolean;
  apiKey: ApiKeyOut;
  setOpen: (open: boolean) => void;
  hook: () => void;
}) => {
  const cancelButtonRef = useRef(null);
  const [deleteApiKey, result] = useDeleteAPIKey();
  const proceed = () => {
    deleteApiKey({ apiKeyId: props.apiKey.id as number });
  };

  //TODO -- handle failure
  React.useEffect(() => {
    if (result.isSuccess) {
      props.setOpen(false);
      props.hook();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result.isSuccess, props.setOpen]);

  return (
    <Transition.Root show={props.open} as={Fragment}>
      <Dialog
        as="div"
        className="relative z-10"
        initialFocus={cancelButtonRef}
        onClose={() => props.setOpen(false)}
      >
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

        <div className="fixed inset-0 z-50 overflow-y-auto">
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
              <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white px-4 pt-5 pb-4 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
                <div className="sm:flex sm:items-start">
                  <div className="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
                    <ExclamationTriangleIcon
                      className="h-6 w-6 text-red-600"
                      aria-hidden="true"
                    />
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                    <Dialog.Title
                      as="h3"
                      className="text-base font-semibold leading-6 text-gray-900"
                    >
                      {`Delete API Key ${props.apiKey.id}`}
                    </Dialog.Title>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500">
                        Deleting your API key can&apos;t be undone -- make sure
                        that you update anything using this!
                      </p>
                    </div>
                  </div>
                </div>
                <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                  <button
                    type="button"
                    className="inline-flex w-full justify-center rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500 sm:ml-3 sm:w-auto"
                    onClick={() => {
                      proceed();
                    }}
                  >
                    Delete
                  </button>
                  <button
                    type="button"
                    className="inline-flex w-full justify-center rounded-md bg-gray-400 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-gray-300 sm:ml-3 sm:w-auto"
                    onClick={() => {
                      props.setOpen(false);
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  );
};

const CreatedAPIKeyDialogue = (props: { apiKey: string }) => {
  const [open, setOpen] = useState(true);

  const CopyButton = () => {
    return (
      <FaCopy
        className="hover:scale-110"
        onClick={() => {
          navigator.clipboard.writeText(props.apiKey);
        }}
      />
    );
  };
  return (
    <Transition.Root show={open} as={Fragment}>
      <Dialog as="div" className="relative z-10" onClose={setOpen}>
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
              <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white px-4 pt-5 pb-4 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl sm:p-6">
                <div>
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
                    <CheckIcon
                      className="h-6 w-6 text-green-600"
                      aria-hidden="true"
                    />
                  </div>
                  <div className="mt-3 text-center sm:mt-5">
                    <Dialog.Title
                      as="h3"
                      className="text-base font-semibold leading-6 text-gray-900"
                    >
                      Created API Key
                    </Dialog.Title>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500">
                        Save this! You will not be able to see it again.
                      </p>
                      <p className="break-all">
                        <code>{props.apiKey}</code>
                      </p>
                    </div>
                  </div>
                </div>
                <div className="mt-5 sm:mt-6">
                  <div className="flex flex-row justify-center">
                    <button className="mx-2 text-gray-500">
                      <CopyButton />
                    </button>
                    <button
                      type="button"
                      className=" px-10 inline-flex max-w-full justify-center rounded-md bg-green-500 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-500"
                      onClick={() => setOpen(false)}
                    >
                      Go back to Api Keys
                    </button>
                  </div>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  );
};

export const ApiKeys = () => {
  const authData = useAppSelector(useAuthData);
  const apiKeys = useAPIKeysFromUser({});
  const loading = authData?.loading || apiKeys.isLoading;
  const [deleteWarningOpen, setDeleteWarningOpen] = useState(false);
  // TODO -- reset this state?
  const [deleteKey, setDeleteKey] = useState<ApiKeyOut | null>(null);
  const [createApiKey, result] = useCreateAPIKey();
  const { userName, userOrg } =
    authData == null || authData.loading
      ? { userName: null, userOrg: null }
      : {
          userName: authData.user?.email,
          userOrg: authData.orgHelper?.getOrgs()[0]?.orgName || "",
        };
  // TODO -- use tags to update state so this is less messy
  React.useEffect(() => {
    apiKeys.refetch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result.data]);
  // TODO -- better handle error cases
  const columns = [
    {
      displayName: "Created",
      Render: (value: ApiKeyOut) => (
        <div>{new Date(value.created_at).toDateString()}</div>
      ),
    },
    {
      displayName: "Name",
      Render: (value: ApiKeyOut) => (
        <div>
          {value.key_name || (userName && DEFAULT_API_KEY_NAME(userName))}
        </div>
      ),
    },
    {
      displayName: "Key",
      Render: (value: ApiKeyOut) => (
        <code>{value.key_start ? `${value.key_start}...` : ""}</code>
      ),
    },
    {
      displayName: "",
      Render: (value: ApiKeyOut) => (
        <div className="flex flex-row justify-end">
          <DeleteButton
            canDelete={true}
            deleteMe={() => {
              setDeleteKey(value);
              setDeleteWarningOpen(true);
            }}
            deleteType={"Delete"}
          />
        </div>
      ),
    },
  ];

  if (loading || userName == null || userOrg == null) {
    return <Loading />;
  }
  const allApiKeys = apiKeys.data || [];
  return (
    <>
      {result.data && <CreatedAPIKeyDialogue apiKey={result.data} />}
      {deleteKey && (
        <DeleteAPIKey
          hook={() => apiKeys.refetch()}
          apiKey={deleteKey}
          open={deleteWarningOpen}
          setOpen={setDeleteWarningOpen}
        />
      )}
      <div className="flex flex-col mt-10">
        <div className="flex flex-row justify-start px-10">
          <button
            onClick={() => {
              // setOpen
              createApiKey({
                apiKeyIn: {
                  name: DEFAULT_API_KEY_NAME(userName),
                },
              });
            }}
            type="button"
            className="inline-flex items-center gap-x-1.5 rounded-md
            bg-green-500 py-2 px-3 text-sm font-semibold text-white shadow-sm
            hover:bg-green-400 focus-visible:outline focus-visible:outline-2
            focus-visible:outline-offset-2 focus-visible:outline-green-500"
          >
            <PlusIcon className="-ml-0.5 h-5 w-5" aria-hidden="true" />
            New API key
          </button>
        </div>
        <GenericTable
          data={allApiKeys.map((apiKey) => [
            apiKey.id?.toString() || "",
            apiKey,
          ])}
          dataTypeName={"ID"}
          columns={columns}
          comparison={(a: [string, ApiKeyOut], b: [string, ApiKeyOut]) => {
            return a[1].created_at > b[1].created_at ? -1 : 1;
          }}
        />
      </div>
    </>
  );
};
