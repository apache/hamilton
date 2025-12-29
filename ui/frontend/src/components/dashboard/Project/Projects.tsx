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

import { Fragment, useEffect, useState } from "react";

import { useNavigate } from "react-router-dom";
import {
  useCreateProject,
  useLatestDAGTemplates,
  useAllProjects,
  useUpdateProject,
  useUserInformation,
  UserInformation,
  Project,
  ProjectWithData,
  getProjectAttributes,
  AttributeDocumentationLoom1,
  useDAGTemplatesByID,
  DAGTemplateWithData,
} from "../../../state/api/friendlyApi";
import { Loading } from "../../common/Loading";
import CreatableSelect from "react-select/creatable";

import { Dialog, Transition } from "@headlessui/react";
import { ErrorPage } from "../../common/Error";
import { GenericTable } from "../../common/GenericTable";
import { NothingToSee, ProjectLogInstructions } from "./ProjectLogInstructions";
import { skipToken } from "@reduxjs/toolkit/dist/query";
import { BiNetworkChart, BiHelpCircle, BiListPlus } from "react-icons/bi";
import { ProjectDocumentation } from "./ProjectDocumentation";
import { PlusIcon } from "@heroicons/react/24/outline";
import { setProjectID } from "../../../state/projectSlice";
import { usePostHog } from "posthog-js/react";
import { VisualizeDAG } from "../Visualize/DAGViz";
import { VizType } from "../Visualize/types";
import { localMode } from "../../../App";

type ProjectCreateFormProps = {
  setOpenProject: (projectId: number) => void;
  whoAmI: UserInformation;
  closeOut: () => void;
  currentProject: Project | null;
  refresh: () => void;
};

const CreatedProjectModal = () => {
  return <div>Success!!</div>;
};
export const ProjectCreateOrEditForm = (props: ProjectCreateFormProps) => {
  const [currentProjectName, setCurrentProjectName] = useState<string>(
    props.currentProject?.name || ""
  );
  const [currentProjectDescription, setCurrentProjectDescription] =
    useState<string>(props.currentProject?.description || "");
  const [createProject, createdProject] = useCreateProject();
  const [updateProject, updatedProject] = useUpdateProject();

  const user = props.whoAmI.user;
  const teams = props.whoAmI.teams;
  // Seed sharing entities with the user
  const userOption = {
    label: user.email,
    kind: "user",
    value: `user-${user.id}`,
    id: user.id as number,
  };
  const defaultVisibleSharingEntities =
    props.currentProject === null
      ? []
      : [
          ...props.currentProject.visibility.teams_visible.map((org) => {
            return {
              label: org.name,
              kind: "org",
              value: `org-${org.id}`,
              id: org.id as number,
            };
          }),
          ...props.currentProject.visibility.users_visible.map((user) => {
            return {
              label: user.email,
              kind: "user",
              value: `user-${user.id}`,
              id: user.id as number,
            };
          }),
        ];

  const defaultWriteSharingEntities =
    props.currentProject === null
      ? [userOption]
      : [
          ...props.currentProject.visibility.teams_writable.map((org) => {
            return {
              label: org.name,
              kind: "org",
              value: `org-${org.id}`,
              id: org.id as number,
            };
          }),
          ...props.currentProject.visibility.users_writable.map((user) => {
            return {
              label: user.email,
              kind: "user",
              value: `user-${user.id}`,
              id: user.id as number,
            };
          }),
        ];

  type PermissionOption = {
    label: string;
    kind: string;
    value: string;
    id: string | number | undefined;
  };

  const [selectedWriteSharingEntities, setSelectedWriteSharingEntities] =
    useState<PermissionOption[]>(defaultWriteSharingEntities);

  const [selectedReadSharingEntities, setSelectedReadSharingEntities] =
    useState<PermissionOption[]>(defaultVisibleSharingEntities);

  const errors = [
    currentProjectName === "" ? "Project name is required" : undefined,
    currentProjectDescription === ""
      ? "Project description is required"
      : undefined,
    selectedWriteSharingEntities.length === 0
      ? "Write access is required by at least one user (or team, if using the enterprise version)"
      : undefined,
  ].filter((item) => item !== undefined);

  const readyToSave = errors.length === 0;

  // selectedReadSharingEntities.length > 0;
  // Quick hack to match the backend for editing public visibility
  // Could just be done through the DB, but its easy enough to do in the UI
  const allowPublicVisibility =
    teams.filter((team) => team.name === "dagworks").length > 0;
  const options = [
    userOption,
    ...teams
      .filter((team) => team.name != "Public" || allowPublicVisibility)
      .map((team) => ({
        label: team.name,
        kind: "team",
        value: `team-${team.id}`,
        id: team.id as number,
      })),
  ];

  const doProjectMutation = () => {
    const body = {
      projectIn: {
        name: currentProjectName,
        description: currentProjectDescription,
        tags: {},
        visibility: {
          team_ids_visible: selectedReadSharingEntities
            .filter((item) => item.kind == "team")
            .map((item) => item.id as number),
          team_ids_writable: selectedWriteSharingEntities
            .filter((item) => item.kind == "team")
            .map((item) => item.id as number),
          user_ids_visible: selectedReadSharingEntities
            .filter((item) => item.kind == "user")
            .map((item) => item.id as number),
          user_ids_writable: selectedWriteSharingEntities
            .filter((item) => item.kind == "user")
            .map((item) => item.id as number),
        },
      },

      // TODO -- fix the BE so we don't accidentally clobber the documentation
      // documentation: props.currentProject?.documentation || [],
    };
    if (props.currentProject === null) {
      createProject(body)
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        .then((result: any) => {
          if (result?.error) {
            console.log(result.error);
          } else {
            props.refresh();
            props.setOpenProject(result.data?.id as number);
          }
        })
        .then(() => props.closeOut());
    } else {
      updateProject({
        projectId: props.currentProject?.id as number,
        bodyParams: {
          attributes: [],
          // TODO -- clean this up so these both use the common shape
          // This is a little awkward
          project: {
            name: body.projectIn.name,
            description: body.projectIn.description,
            tags: body.projectIn.tags,
            visibility: body.projectIn.visibility,
          },
        },
        // typescript does not like the return type here
      })
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        .then((result: any) => {
          if (result?.error) {
            console.log(result.error);
          } else {
            props.refresh();
            props.setOpenProject(result.data?.id as number);
          }
        })
        .then(() => props.closeOut());
    }
  };

  if (!createdProject.isUninitialized || !updatedProject.isUninitialized) {
    if (createdProject.isLoading || updatedProject.isLoading) {
      return <Loading />;
    }
    if (createdProject.isError || updatedProject.isError) {
      return <ErrorPage message="Failed to update project" />;
    }
    if (createdProject.isSuccess || updatedProject.isSuccess) {
      return (
        <CreatedProjectModal
        // project={createdProject.data || (updatedProject.data as Project)}
        />
      );
    }
    return <></>;
  }

  return (
    <div>
      <div className="space-y-12 w-144  pb-12">
        <div className="border-b border-gray-900/10">
          <p className="mt-1 text-sm leading-6 text-gray-600 w-full">
            Track execution of DAGs, visualize your pipelines, and understand
            how they change over time!
          </p>

          <div className="mt-10 grid grid-cols-1 gap-x-6 gap-y-8 sm:grid-cols-6">
            <div className="sm:col-span-4">
              <label className="block text-sm font-medium leading-6 text-gray-900">
                Project Name
              </label>
              <div className="mt-2">
                <div
                  className="flex rounded-md shadow-sm ring-1 ring-inset ring-gray-300 focus-within:ring-2
                    focus-within:ring-inset focus-within:ring-dwdarkblue sm:max-w-md"
                >
                  <input
                    type="text"
                    className="block flex-1 border-0 bg-transparent py-1.5 pl-2 text-gray-900 placeholder:text-gray-400
                    focus:ring-0 sm:text-sm sm:leading-6"
                    value={currentProjectName || ""}
                    onChange={(e) => setCurrentProjectName(e.target.value)}
                    placeholder="Your project name"
                  />
                </div>
              </div>
            </div>

            <div className="col-span-full">
              <label
                htmlFor="about"
                className="block text-sm font-medium leading-6 text-gray-900"
              >
                Project Description
              </label>
              <div className="mt-2">
                <textarea
                  id="about"
                  name="about"
                  rows={3}
                  value={currentProjectDescription || ""}
                  onChange={(e) => setCurrentProjectDescription(e.target.value)}
                  className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-dwdarkblue sm:text-sm sm:leading-6"
                  placeholder={"Project description in markdown..."}
                />
              </div>
            </div>
            <div className="col-span-full">
              <label
                htmlFor="about"
                className="block text-sm font-medium leading-6 text-gray-900"
              >
                Read Access
              </label>
              <p className="mt-1 text-sm leading-6 text-gray-600 w-full">
                Enter emails
                {localMode ? " (reach out if you want team/organization-level ACLs)" : " or select teams you are part of."}.
              </p>
              <div className="mt-2">
                <CreatableSelect
                  isMulti
                  options={options}
                  value={selectedReadSharingEntities}
                  onChange={(selected) => {
                    setSelectedReadSharingEntities(Array.from(selected));
                    // BE doesn't like having it in both, for now just move it from one to the other
                    setSelectedWriteSharingEntities(
                      selectedWriteSharingEntities.filter(
                        (item) =>
                          !selected
                            .map((i) => i.value === item.value)
                            .some((i) => i)
                      )
                    );
                  }}
                  formatCreateLabel={(value) => `Add ${value}`}
                  onCreateOption={(inputValue) => {
                    const newOption = {
                      label: inputValue,
                      value: `user-${inputValue}`,
                      id: inputValue,
                      kind: "user",
                    };

                    setSelectedReadSharingEntities([
                      ...selectedWriteSharingEntities,
                      newOption,
                    ]);
                    setSelectedWriteSharingEntities(
                      selectedWriteSharingEntities.filter(
                        (item) => newOption.label !== item.label
                      )
                    );
                  }}
                />
              </div>
            </div>
            <div className="col-span-full">
              <label
                htmlFor="about"
                className="block text-sm font-medium leading-6 text-gray-900"
              >
                Write Access
              </label>
              <p className="mt-1 text-sm leading-6 text-gray-600 w-full">
                Enter emails
                {localMode ? " (reach out if you want team/organization-level ACLs)" : " or select teams you are part of."}.
              </p>
              <div className="mt-2">
                <CreatableSelect
                  isMulti
                  options={options}
                  value={selectedWriteSharingEntities}
                  onChange={(selected) => {
                    setSelectedWriteSharingEntities(Array.from(selected));
                    setSelectedReadSharingEntities(
                      selectedReadSharingEntities.filter(
                        (item) =>
                          !selected
                            .map((i) => i.value === item.value)
                            .some((i) => i)
                      )
                    );
                  }}
                  onCreateOption={(inputValue) => {
                    const newOption = {
                      label: inputValue,
                      value: `user-${inputValue}`,
                      id: inputValue,
                      kind: "user",
                    };

                    setSelectedWriteSharingEntities([
                      ...selectedWriteSharingEntities,
                      newOption,
                    ]);
                    setSelectedReadSharingEntities(
                      selectedReadSharingEntities.filter(
                        (item) => newOption.label !== item.label
                      )
                    );
                  }}
                />
              </div>
            </div>
          </div>
          <div className="pb-2">
            {errors.map((error) => (
              <p className="mt-2 text-sm text-dwred" key={error}>
                ❗{error}
              </p>
            ))}
          </div>
        </div>
      </div>
      <div className="mt-6 flex items-center justify-end gap-x-6">
        <button
          type="button"
          className="text-sm font-semibold leading-6 text-gray-900"
          onClick={() => {
            props.closeOut();
          }}
        >
          Cancel
        </button>
        <button
          disabled={!readyToSave}
          onClick={() => {
            doProjectMutation();
          }}
          className={`rounded-md bg-dwdarkblue px-3 py-2 text-sm font-semibold text-white shadow-sm
           hover:bg-dwdarkblue/80 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2
           focus-visible:outline-dwdarkblue ${readyToSave ? "" : "opacity-50"}`}
        >
          {props.currentProject === null ? "Create" : "Save"}
        </button>
      </div>
    </div>
  );
};

const ProjectCreateOrEditModal = (props: {
  open: boolean;
  closeModal: () => void;
  refresh: () => void;
  // If ExistingProject is null, this is create
  // If it is "edit", this is edit
  existingProject: ProjectWithData | null;
  setOpenProject: (projectId: number) => void;
}) => {
  const { open, refresh, closeModal } = props;
  const whoAmIInfo = useUserInformation();
  if (whoAmIInfo.isLoading) {
    return <Loading />;
  }
  if (whoAmIInfo.isError) {
    return <ErrorPage message={"Unable to load user information"} />;
  }
  // TODO -- ensure that this can't be null
  const whoAmI = whoAmIInfo.data as UserInformation;

  return (
    <Transition.Root show={open} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={closeModal}>
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
              <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white px-4 pt-5 pb-4 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-max sm:p-6">
                <div>
                  <div className="">
                    <Dialog.Title
                      as="h2"
                      className=" font-semibold leading-6 text-gray-900 text-xl"
                    >
                      {!props.existingProject
                        ? "Create a new project"
                        : `Edit project: ${props.existingProject.name}`}
                    </Dialog.Title>
                    <ProjectCreateOrEditForm
                      setOpenProject={props.setOpenProject}
                      whoAmI={whoAmI}
                      closeOut={closeModal}
                      refresh={refresh}
                      currentProject={props.existingProject}
                    />
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
const isProjectDemo = (project: ProjectWithData) => {
  const permissions = project.visibility.teams_visible;
  return permissions.some((team) => team.name === "Public");
};
export const ProjectsView = () => {
  // TODO -- add pagination...
  const { data, isError, isFetching, refetch } = useAllProjects({
    limit: 1000,
    offset: 0,
    attributeTypes: "documentation_loom",
  });
  const whoAmIInfo = useUserInformation();
  const email = whoAmIInfo.data?.user.email || "";

  const projects = data as ProjectWithData[];

  const [open, setOpen] = useState(false);

  useEffect(() => {
    // Get the query string from the URL
    const queryString = window.location.search;

    // Parse the query string to extract parameters
    const urlParams = new URLSearchParams(queryString);

    // Check if the 'new' parameter exists and has a value of 'true'
    if (urlParams.get("new") === "true") {
      setOpen(true);
    }
  }, []);

  const [currentlyEditing, setCurrentlyEditing] =
    useState<ProjectWithData | null>(null);
  const [expandedProject, setExpandedProject] = useState<number | undefined>(
    undefined
  );

  const [expandedView, setExpandedView] = useState<"dag" | "write" | "docs">();
  const toggleExpandedView = (
    view: "dag" | "write" | "docs",
    projectId: number
  ) => {
    if (expandedProject === projectId) {
      if (expandedView === view) {
        setExpandedProject(undefined);
      }
    } else {
      setExpandedProject(projectId);
    }
    setExpandedView(view);
  };
  // TODO -- add the ability to load everything to the API, then we wouldn't have to do both
  const expandedDAGTemplate = useLatestDAGTemplates(
    expandedProject !== undefined
      ? { projectId: expandedProject, limit: 1 }
      : skipToken
  );
  const expandedDAGTemplateWithFullData = useDAGTemplatesByID(
    expandedDAGTemplate.data?.[0] !== undefined
      ? { dagTemplateIds: `${expandedDAGTemplate.data[0]?.id}` }
      : skipToken
  );
  const navigate = useNavigate();
  const posthog = usePostHog();

  if (isFetching) {
    return <Loading />;
  } else if (isError) {
    return <ErrorPage message="Unable to load projects" />;
  }

  const projectCols = [
    {
      displayName: "Name",
      Render: (project: ProjectWithData) => {
        if (isProjectDemo(project)) {
          return (
            <div className="flex flex-row text-sm w-[14rem] truncate text-gray-900 gap-2 items-center ">
              <span className="text-xs text-white bg-yellow-400 p-1 px-2 rounded-lg">
                Demo
              </span>
              {project.name}
            </div>
          );
        }
        return (
          <div className="text-sm w-[14rem] truncate text-gray-900">
            {project.name}
          </div>
        );
      },
    },
    {
      displayName: "Created",
      Render: (project: ProjectWithData) => {
        return (
          <div className="text-sm text-gray-900">
            {new Date(project.created_at).toLocaleDateString()}
          </div>
        );
      },
    },
    {
      displayName: "Updated",
      Render: (project: ProjectWithData) => {
        return (
          <div className="text-sm text-gray-900">
            {new Date(project.updated_at).toLocaleDateString()}
          </div>
        );
      },
    },
    // TODO: clean this up so description looks nice on projects page.
    // {
    //   displayName: "Description",
    //   Render: (project: ProjectOut) => {
    //     const [showFullDescription, setShowFullDescription] = useState(false);
    //     return (
    //       <div
    //         className={`w-52 ${
    //           showFullDescription ? "whitespace-pre-wrap" : ""
    //         } cursor-cell`}
    //         onClick={() => {
    //           setShowFullDescription(!showFullDescription);
    //         }}
    //       >
    //         {showFullDescription ? (
    //           <div className="">
    //             <ReactMarkdown className="prose">
    //               {project.description}
    //             </ReactMarkdown>
    //           </div>
    //         ) : (
    //           <div className=" cursor-cell truncate">...</div>
    //         )}{" "}
    //       </div>
    //     );
    //   },
    // },
    // {
    //   displayName: "Created By",
    //   Render: (project: Project) => {
    //     return (
    //       <div className="text-sm text-gray-900 break">{project.}</div>
    //     );
    //   },
    // },
    {
      displayName: "",
      Render: (project: ProjectWithData) => {
        const disabled = project.role !== "write";
        return (
          <button
            disabled={disabled}
            onClick={() => {
              setCurrentlyEditing(project);
              setOpen(true);
            }}
            type="button"
            className={`inline-flex justify-center items-center gap-x-2 rounded-md ${
              disabled ? "bg-dwlightblue/50" : "bg-dwlightblue"
            } py-2 px-3.5 w-16
            text-sm font-semibold text-white shadow-sm hover:bg-dwlightblue/80 focus-visible:outline focus-visible:outline-2
            focus-visible:outline-offset-2 focus-visible:outline-dwlightblue`}
            title="Edit project details and access."
          >
            Edit
          </button>
        );
      },
    },
    {
      displayName: "",
      Render: (project: ProjectWithData) => {
        return (
          <button
            onClick={() => {
              navigate(`/dashboard/project/${project.id}`);
              setProjectID(project.id as number);
            }}
            type="button"
            className="inline-flex justify-center items-center gap-x-2 rounded-md bg-green-500 py-2 px-2.5 w-16
      text-sm font-semibold text-white shadow-sm hover:bg-green-500/80 focus-visible:outline focus-visible:outline-2
      focus-visible:outline-offset-2 focus-visible:outline-green-500"
            title="View the project."
          >
            {isProjectDemo(project) ? "Explore" : "View"}
          </button>
        );
      },
    },
    {
      displayName: "",
      Render: (project: ProjectWithData) => {
        const ExpandIcon = BiNetworkChart;
        return (
          <ExpandIcon
            className="text-xl hover:scale-125 cursor-pointer"
            title="View the project's DAG"
            onClick={() => {
              toggleExpandedView("dag", project.id as number);
            }}
          />
        );
      },
    },
    {
      displayName: "",
      Render: (project: ProjectWithData) => {
        const ExpandIcon = BiListPlus;
        const canWrite = project.role === "write";
        return (
          <ExpandIcon
            className={`text-xl ${
              canWrite ? "hover:scale-125 cursor-pointer" : "text-gray-300"
            }`}
            title="Quick start instructions."
            onClick={() => {
              if (!canWrite) {
                return;
              }
              toggleExpandedView("write", project.id as number);
            }}
          />
        );
      },
    },
    {
      displayName: "",
      Render: (project: ProjectWithData) => {
        const ExpandIcon = BiHelpCircle;
        const documentation = getProjectAttributes<AttributeDocumentationLoom1>(
          project.attributes,
          "AttributeDocumentationLoom1"
        );
        return (
          <ExpandIcon
            className={
              documentation.length > 0
                ? "text-xl hover:scale-125 cursor-pointer"
                : "opacity-0"
            }
            title="Watch video about this project."
            onClick={() => {
              toggleExpandedView("docs", project.id as number);
            }}
          />
        );
      },
    },
  ];
  const projectsSorted = [...projects].sort((a, b) => {
    const aIsDemo = isProjectDemo(a);
    const bIsDemo = isProjectDemo(b);
    // Quick hack to put demo projects at the bottom for everyone except dagworks members
    // or whom they go wherever
    if (
      (whoAmIInfo.data?.teams || []).filter((team) => team.name === "dagworks")
        .length === 0
    ) {
      if (aIsDemo && !bIsDemo) {
        return 1;
      }
      if (!aIsDemo && bIsDemo) {
        return -1;
      }
    }

    return a.updated_at > b.updated_at ? -1 : 1;
  });

  return (
    <div className="mt-10">
      <button
        onClick={() => {
          // setOpen
          posthog?.capture("click-project-details", {
            step: currentlyEditing ? "edit" : "create",
          });
          setOpen(true);
          // Get the current URL
          const currentURL = new URL(window.location.href);

          // Add or update the 'new' parameter to the URL
          currentURL.searchParams.set("new", "true");

          // Update the URL with the modified query parameters
          window.history.pushState(null, "", currentURL.toString());
        }}
        type="button"
        title="Create a new project"
        className="inline-flex items-center gap-x-1.5 rounded-md ml-8
            bg-green-500 py-2 px-3 text-sm font-semibold text-white shadow-sm
            hover:bg-green-400 focus-visible:outline focus-visible:outline-2
            focus-visible:outline-offset-2 focus-visible:outline-green-500"
      >
        <PlusIcon className="-ml-0.5 h-5 w-5" aria-hidden="true" />
        New Project
      </button>
      <ProjectCreateOrEditModal
        open={open}
        refresh={refetch}
        setOpenProject={(projectId: number) => {
          setExpandedProject(projectId);
        }}
        closeModal={() => {
          const promise = new Promise((resolve) => setTimeout(resolve, 200));
          // Get the current URL
          const currentURL = new URL(window.location.href);

          // Remove the 'new' parameter from the URL
          currentURL.searchParams.delete("new");

          // Update the URL with the modified query parameters
          window.history.pushState(null, "", currentURL.toString());
          setOpen(false);
          // Stupid hack as it displays the wrong modal
          // Better way to do this is to separate out the modal between create and edit
          promise.then(() => {
            setCurrentlyEditing(null);
          });
        }}
        existingProject={currentlyEditing} // This is a create project
      />
      <GenericTable
        data={projectsSorted.map((item) => [
          item.id?.toString() as string,
          item,
        ])}
        columns={projectCols}
        dataTypeName="Project ID"
        extraRowData={{
          shouldRender: (project: ProjectWithData) =>
            project.id === expandedProject,
          Render: (props: { value: ProjectWithData }) => {
            const project = props.value;
            const writeView = (
              <div className="flex justify-center py-5">
                <ProjectLogInstructions
                  canWrite={project.role === "write"}
                  projectId={project.id as number}
                  username={email}
                  hideAPIKey={localMode}
                />
              </div>
            );
            const documentation =
              getProjectAttributes<AttributeDocumentationLoom1>(
                project.attributes,
                "AttributeDocumentationLoom1"
              );
            const docView = <ProjectDocumentation loomDocs={documentation} />;
            if (expandedView === "write") {
              return writeView;
            }
            if (expandedView === "docs") {
              return docView;
            }
            if (
              expandedDAGTemplate.isFetching ||
              expandedDAGTemplate.isLoading ||
              expandedDAGTemplateWithFullData.isFetching ||
              expandedDAGTemplateWithFullData.isLoading
            ) {
              return (
                <div className="flex justify-center py-5">
                  <Loading />
                </div>
              );
            }
            if (
              expandedDAGTemplate.data === undefined ||
              expandedDAGTemplate.data.length === 0
            ) {
              if (project.role === "write") {
                return writeView;
              }
              return <NothingToSee />;
            }
            return (
              <div className="">
                {expandedDAGTemplateWithFullData.data?.[0] && (
                  <VisualizeDAG
                    height={"h-[600px]"}
                    enableLineageView={false}
                    enableVizConsole={false}
                    templates={[
                      expandedDAGTemplateWithFullData
                        .data?.[0] as DAGTemplateWithData,
                    ]}
                    runs={undefined}
                    vizType={VizType.StaticDAG}
                    displayLegend={false}
                    enableGrouping={false}
                    displayMiniMap={false}
                    displayControls={true}
                  />
                )}
              </div>
            );
          },
        }}
      />
    </div>
  );
};
