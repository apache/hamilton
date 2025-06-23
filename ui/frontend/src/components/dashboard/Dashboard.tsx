import { useState } from "react";
import {
  FolderIcon,
  QuestionMarkCircleIcon,
  ArrowRightOnRectangleIcon,
  MagnifyingGlassIcon,
  IdentificationIcon,
} from "@heroicons/react/24/outline";
import { NAV_HELP, navKeys, resolveNav } from "./nav";
import { GoTriangleDown, GoTriangleRight } from "react-icons/go";
import { useAppSelector } from "../../state/hooks";
import {
  Link,
  Outlet,
  useLocation,
  useNavigate,
  useOutletContext,
} from "react-router-dom";
import { Loading } from "../common/Loading";

import { useAuthData } from "../../state/authSlice";
import { useLogoutFunction } from "@propelauth/react";
import { ChevronLeftIcon, ChevronRightIcon } from "@heroicons/react/20/solid";
import { IoKeyOutline } from "react-icons/io5";
import { HelpVideos } from "../tutorial/HelpVideo";
import { WithHelpIcon } from "../common/WithHelpIcon";
import { TbDelta } from "react-icons/tb";
import {
  DAGTemplateWithData,
  DAGTemplateWithoutData,
  ProjectWithData,
  useDAGTemplatesByID,
  useLatestDAGTemplates,
  useProjectByID,
} from "../../state/api/friendlyApi";
import { useURLParams } from "../../state/urlState";
import { NavBreadCrumb } from "./NavBreadCrumb";
import { skipToken } from "@reduxjs/toolkit/dist/query";
import { SearchBar } from "./Search/search";
import { ErrorPage } from "../common/Error";
import { IconType } from "react-icons";
import { localMode } from "../../App";
import { localLogout } from "../../auth/Login";

const useProcessAwareLogout = () => {
  if (process.env.REACT_APP_AUTH_MODE === "local") {
    return (redirectOnLogin: boolean) => {
      return new Promise<void>(() => {
        localLogout(redirectOnLogin);
      });
    };
  }
  // eslint-disable-next-line
  return useLogoutFunction();
};

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(" ");
}

export const FeedbackButton = (props: { userName: string }) => {
  return (
    <button
      data-feedback-fish
      data-feedback-fish-url={window.location.href}
      data-feedback-fish-userid={props.userName}
      className="cursor-pointer select-none rounded-full py-2 px-5 bg-yellow-400 text-gray-900"
    >
      Feedback
    </button>
  );
};

const SubMenu = (props: {
  name: string;
  navigate: (href: string) => void;
  items: { href: string; name: string; current: boolean; icon: IconType }[];
  disable: boolean;
}) => {
  const { name, items, navigate } = props;
  const anyCurrent = items.some((item) => item.current);
  const [isExpanded, setExpanded] = useState(false || anyCurrent);
  const ExpandIcon = isExpanded ? GoTriangleDown : GoTriangleRight;
  const out = (
    <>
      <div
        onClick={() => setExpanded(!isExpanded)}
        className={classNames(
          `${
            props.disable
              ? "text-gray-400"
              : "text-gray-300 hover:bg-gray-700 hover:text-white"
          }`,
          "group flex justify-between items-center px-2 py-2 text-base font-medium rounded-md"
        )}
      >
        {name}
        {props.disable ? <></> : <ExpandIcon className="cursor-pointer" />}
      </div>
      {isExpanded &&
        items.map((item) => {
          return (
            <div
              key={item.name}
              onClick={() => navigate(item.href)}
              className={classNames(
                item?.current
                  ? "bg-gray-900 text-white"
                  : "text-gray-300 hover:bg-gray-700 hover:text-white",
                "group flex items-center px-2 py-2 text-base font-medium rounded-md"
              )}
            >
              <item.icon
                className={classNames(
                  item?.current
                    ? "text-gray-300"
                    : "text-gray-400 group-hover:text-gray-300",
                  "mr-4 flex-shrink-0 h-6 w-6"
                )}
                aria-hidden="true"
              />
              {item.name}
            </div>
          );
        })}
    </>
  );
  return (
    <WithHelpIcon
      whichIcon={
        NAV_HELP[name as keyof typeof NAV_HELP] as keyof typeof HelpVideos
      }
      translate="-translate-x-2 translate-y-3"
    >
      {out}
    </WithHelpIcon>
  );
};

const TopLevelMenu = (props: {
  navigate: (href: string) => void;
  item: { href: string; name: string; current: boolean; icon: IconType };
  disable: boolean;
}) => {
  const { navigate } = props;
  const out = (
    <>
      <div
        key={props.item.name}
        onClick={() => navigate(props.item.href)}
        className={classNames(
          props.item?.current
            ? "bg-gray-900 text-white"
            : "text-gray-300 hover:bg-gray-700 hover:text-white",
          "hover:cursor-pointer select-none group flex items-center px-2 py-2 text-base font-medium rounded-md"
        )}
      >
        <props.item.icon
          className={classNames(
            props.item?.current
              ? "text-gray-300"
              : "text-gray-400 group-hover:text-gray-300",
            "mr-4 flex-shrink-0 h-6 w-6"
          )}
          aria-hidden="true"
        />
        {props.item.name}
      </div>
    </>
  );
  const hasHelpVideo =
    NAV_HELP[props.item.name as keyof typeof NAV_HELP] !== undefined;
  if (hasHelpVideo) {
    return (
      <WithHelpIcon
        whichIcon={
          NAV_HELP[
            props.item.name as keyof typeof NAV_HELP
          ] as keyof typeof HelpVideos
        }
        translate="-translate-x-2 translate-y-3"
      >
        {out}
      </WithHelpIcon>
    );
  }
  return out;
};

export const API_KEY_ICON = IoKeyOutline;

const MiniSideBar = (props: {
  toggleMinimize: () => void;
  setSearchBarOpen: () => void;
  logout: ((redirect: boolean) => void) | null;
}) => {
  const navigate = useNavigate();
  return (
    <div className="w-20 h-full border-r-gray-700 border-r-2">
      <div className="flex flex-col mt-6 h-full items-center gap-3">
        <img
          src="/logo.png"
          className={classNames("hover:cursor-pointer", " h-10 w-10")}
          aria-hidden="true"
          title="Open/Close Side Bar"
          onClick={() => props.toggleMinimize()}
        />
        <WithHelpIcon
          whichIcon="PROJECT_SELECTOR"
          translate="-translate-x-3 translate-y-3"
        >
          <FolderIcon
            onClick={() => navigate("/dashboard/projects")}
            className="text-gray-300 hover:bg-gray-700 hover:text-white hover:cursor-pointer rounded-md h-10 w-10"
            aria-hidden="true"
            title="Projects"
          />
        </WithHelpIcon>
        <MagnifyingGlassIcon
          onClick={() => props.setSearchBarOpen()}
          className={classNames(
            "text-gray-300 hover:bg-gray-700 hover:text-white hover:cursor-pointer rounded-md border-0 border-transparent",
            " h-10 w-10"
          )}
          aria-hidden="true"
          title="Search"
        />
        <a
          href="https://hamilton.apache.org/concepts/ui"
          target="_blank"
          rel="noopener noreferrer"
        >
          <QuestionMarkCircleIcon
            className={classNames(
              "text-gray-300 hover:bg-gray-700 hover:text-white hover:cursor-pointer rounded-md",
              "h-10 w-10"
            )}
            aria-hidden="true"
            title="Getting Started Guide"
          />
        </a>
        <div>
          {!localMode && (
            <WithHelpIcon
              whichIcon="API_KEYS"
              translate="-translate-x-3 translate-y-3"
            >
              {
                <API_KEY_ICON
                  onClick={() => navigate("/dashboard/settings")}
                  className={classNames(
                    "text-gray-300 hover:bg-gray-700 hover:text-white hover:cursor-pointer rounded-md border-0 border-transparent",
                    " h-10 w-10"
                  )}
                  aria-hidden="true"
                  title="API Keys"
                />
              }
            </WithHelpIcon>
          )}
        </div>
        <div>
          <Link to="/dashboard/account">
            <IdentificationIcon
              className={classNames(
                "text-gray-300 hover:bg-gray-700 hover:text-white hover:cursor-pointer rounded-md border-0 border-transparent",
                " h-10 w-10"
              )}
              title="Account Settings"
            />
          </Link>
        </div>
        <div onClick={() => (props.logout ? props.logout : () => void 0)(true)}>
          {
            <ArrowRightOnRectangleIcon
              className={classNames(
                "text-gray-300 hover:bg-gray-700 hover:text-white hover:cursor-pointer rounded-md",
                " h-10 w-10"
              )}
              aria-hidden="true"
              title="Logout"
            />
          }
        </div>
      </div>
    </div>
  );
};

const MinimizeButton = (props: {
  toggleMinimize: () => void;
  color: "white" | "grey";
  kind: "open" | "close";
}) => {
  const Icon = props.kind === "close" ? ChevronLeftIcon : ChevronRightIcon;
  return (
    <button
      type="button"
      className={`ml-1 flex h-10 w-10 items-center justify-center rounded-full
          focus:outline-none focus:ring-2 focus:ring-inset mb-2 ${
            props.color == "white"
              ? "focus:ring-white"
              : "focus:ring-dwdarkblue/40"
          }`}
      onClick={() => props.toggleMinimize()}
    >
      <span className="sr-only">Close sidebar</span>
      <Icon
        className={`h-6 w-6 ${
          props.color == "white" ? "text-white" : "text-dwdarkblue/40"
        }`}
        aria-hidden="true"
      />
    </button>
  );
};
const ProjectAwareSidebar = (props: {
  setMinimized: () => void;
  projectName: string;
  dagTemplates: DAGTemplateWithoutData[];
  projectId: number | undefined;
  navSubMenus: {
    header: string;
    menus: {
      href: string;
      name: string;
      current: boolean;
      icon: IconType;
      under: string;
    }[];
  }[];
  topLevelNavs: {
    href: string;
    name: string;
    current: boolean;
    icon: IconType;
  }[];
  navigate: (path: string) => void;
  userName: string;
  userOrg: string;
}) => {
  const navKeys = props.navSubMenus.map((item) => item.header);
  // const navKeys = [...props.navSubMenus.map((item) => item.header)];
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex flex-1 flex-col overflow-y-auto py-4">
        <div className="border-b-2 border-b-gray-700 px-3 pb-2">
          <Link
            to={`/dashboard/project/${props.projectId}`}
            className="text-gray-300 hover:underline select-none"
          >
            {props.projectName}
          </Link>
          {props.dagTemplates.length > 0 ? (
            <div className="text-gray-300 font-semibold flex flex-row gap-1 items-center">
              {props.dagTemplates.flatMap((v, i) => {
                const isLast = i === props.dagTemplates.length - 1;
                const vNumber = (
                  <Link
                    className="hover:cursor-pointer select-none hover:text-white hover:underline"
                    to={`/dashboard/project/${props.projectId}/versions`}
                    key={v.id}
                  >
                    version {v.id}
                  </Link>
                );
                const joined = <TbDelta className="" />;
                return isLast ? [vNumber] : [vNumber, joined];
              })}
            </div>
          ) : null}
        </div>
        <nav className="flex-1 space-y-1 mx-2 mt-1">
          {props.topLevelNavs.map((item, i) => (
            <TopLevelMenu
              key={i}
              item={item}
              navigate={props.navigate}
              disable={false}
            />
          ))}
          {navKeys.map((key, i) => {
            return (
              <SubMenu
                name={key as string}
                key={i}
                items={props.navSubMenus[i].menus}
                navigate={props.navigate}
                disable={props.navSubMenus[i].menus.length === 0}
              />
            );
          })}
        </nav>
      </div>
      <div className="w-48 px-3 py-3">
        <div className="flex flex-shrink-0 items-center pb-8">
          <div className="ml-3">
            <p className="text-base font-medium text-white truncate w-48">
              {props.userName}
            </p>
            <p className="font-medium text-gray-400 group-hover:text-gray-300">
              {props.userOrg}
            </p>
          </div>
        </div>
        <FeedbackButton userName={props.userName}></FeedbackButton>
      </div>
    </div>
  );
};

const SideBar = (props: {
  allowMinimization: boolean;
  full: boolean;
  navSubMenus: {
    header: string;
    menus: {
      href: string;
      name: string;
      current: boolean;
      icon: IconType;
      under: string;
    }[];
  }[];
  topLevelNavs: {
    href: string;
    name: string;
    current: boolean;
    icon: IconType;
  }[];
  userName: string;
  userOrg: string;
  navigate: (path: string) => void;
  setSearchBarOpen: () => void;
  projectName: string;
  dagTemplates: DAGTemplateWithoutData[];
  projectId: number | undefined;
}) => {
  const {
    navSubMenus,
    topLevelNavs,
    userName,
    userOrg,
    navigate,
    setSearchBarOpen,
    projectName,
    allowMinimization,
  } = props;
  const logoutBase = useProcessAwareLogout();
  const logout = logoutBase
    ? (redirectOnLogin: boolean) => {
        logoutBase(redirectOnLogin).then(() => {
          // Quick way to reset state
          localStorage.clear();
        });
      }
    : null;
  const [displayProjectSidebar, setDisplayProjectSidebar] = useState(true);
  return (
    <>
      {allowMinimization && (
        <div className="absolute bottom-2 left-3 z-50">
          <MinimizeButton
            kind={displayProjectSidebar ? "close" : "open"}
            toggleMinimize={() =>
              setDisplayProjectSidebar(!displayProjectSidebar)
            }
            color={"white"}
          />
        </div>
      )}
      <div className="flex flex-row h-full bg-gray-800">
        {/* General project nav -- this toggles between project select view and team view */}
        <MiniSideBar
          setSearchBarOpen={setSearchBarOpen}
          logout={logout}
          toggleMinimize={() =>
            setDisplayProjectSidebar(!displayProjectSidebar)
          }
        />
        {props.full && displayProjectSidebar && (
          <ProjectAwareSidebar
            setMinimized={() => setDisplayProjectSidebar(false)}
            projectName={projectName}
            dagTemplates={props.dagTemplates}
            navSubMenus={navSubMenus}
            topLevelNavs={topLevelNavs}
            navigate={navigate}
            userName={userName}
            userOrg={userOrg}
            projectId={props.projectId}
          />
        )}
      </div>
    </>
  );
};

type ContextType = {
  dagTemplates: DAGTemplateWithData[];
  project: ProjectWithData;
};

export const useData = () => {
  return useOutletContext<ContextType>();
};

const Dashboard = () => {
  /**
   * State for the dashboard.
   * Most of this is delegated to the subcomponents.
   */
  const [searchBarOpen, setSearchBarOpen] = useState(false);
  const { versionIds, projectId } = useURLParams();
  const navigate = useNavigate();
  const whereAmI = useLocation();
  const authData = useAppSelector(useAuthData);

  /**
   * Navigation/outlets.
   * We redirect to the project selection page if the user has not chosen a project.
   * This is actually just... this page without the sidebar.
   *
   * Outlets are configured in the router in App.tsx.
   */
  const hasChosenProject = projectId !== undefined;

  /**
   * If we have not chosen a project, we have no business being here.
   */
  const project = useProjectByID(
    projectId !== undefined
      ? {
          projectId: projectId,
          attributeTypes: ["documentation_loom"].join(","),
        }
      : skipToken
  );

  const dagTemplateVersions = useDAGTemplatesByID(
    versionIds !== undefined
      ? {
          dagTemplateIds: versionIds.join(","),
        }
      : skipToken
  );

  // These are a little funky -- we get the latest version just so we have somewhere
  // to get in the nav, in case the user wants to click "code" or "visualize"
  const latestProjectVersion = useLatestDAGTemplates(
    versionIds === undefined && projectId !== undefined
      ? {
          limit: 1,
          projectId: projectId,
        }
      : skipToken
  );

  const latestProjectVersionFull = useDAGTemplatesByID(
    latestProjectVersion?.data !== undefined
      ? {
          dagTemplateIds: latestProjectVersion?.data.map((i) => i.id).join(","),
        }
      : skipToken
  );
  // if (!hasChosenProject) {
  //   return <Navigate to="/dashboard/projects" />;
  // }

  // if (!hasChosenDAGTemplateVersions) {
  //   return <Navigate to={`/dashboard/project/${projectId}/versions`} />;
  // }

  const getElement = () => {
    const loading =
      authData?.loading ||
      project.isLoading ||
      project.isFetching ||
      dagTemplateVersions.isLoading ||
      dagTemplateVersions.isFetching;
    if (loading) {
      return <Loading />;
    }
    const error = project.error || dagTemplateVersions.error;
    if (error) {
      return <ErrorPage message={"Failed to load data"} />;
    }
    return (
      <Outlet
        context={{
          dagTemplates: dagTemplateVersions.data,
          project: project.data as ProjectWithData,
        }}
      />
    );
  };

  // Quick way to tell where we are/whether we should display the full sidebar or just the mini one
  const canDisplayFullSidebar = // TODO: break the app into three levels.
    whereAmI.pathname.startsWith("/dashboard/project/");
  const { userName, userOrg } =
    authData == null || authData.loading
      ? { userName: "", userOrg: "" }
      : {
          userName: authData.user?.email,
          userOrg: authData.orgHelper?.getOrgs()[0]?.orgName || "",
        };

  /**
   * Menus/sidebar lists -- everything is configured from nav.ts
   */
  const navResolved = resolveNav(
    project.data?.id?.toString(),
    dagTemplateVersions?.data || latestProjectVersionFull?.data
  );
  const topLevelNavs = navResolved
    .filter((item) => item.under === null)
    .map((navMenu) => {
      return {
        ...navMenu,
        current: navMenu.href === whereAmI.pathname,
      };
    });
  const navSubMenus = navKeys.map((key) => {
    return {
      header: key,
      menus: navResolved
        .filter((item) => item.under === key)
        .map((item) => {
          return {
            ...item,
            current: item.href === whereAmI.pathname,
            under: key,
          };
        }),
    };
  });
  return (
    <>
      <SearchBar open={searchBarOpen} setOpen={setSearchBarOpen} />
      <div className="flex flex-row overflow-y-clip overscroll-none">
        <div className="md:flex md:flex-col z-50 sticky top-0 h-screen overflow-y-clip">
          {/* Sidebar component, swap this element with another sidebar if you like */}
          <SideBar
            allowMinimization={canDisplayFullSidebar}
            full={canDisplayFullSidebar}
            navSubMenus={navSubMenus}
            topLevelNavs={topLevelNavs}
            userName={userName || ""}
            userOrg={userOrg || ""}
            navigate={navigate}
            setSearchBarOpen={() => setSearchBarOpen(true)}
            projectName={project.data?.name || ""}
            dagTemplates={dagTemplateVersions?.data || []}
            projectId={projectId}
          />
        </div>
        <div className="flex flex-1 flex-col">
          <main className="flex-1 px-4">
            {dagTemplateVersions.isSuccess &&
              project.isSuccess &&
              project.data !== null && // TODO -- determine if this could be null?
              hasChosenProject && (
                <div className="fixed top-0 px-4 sm:px-6 md:px-8 py-4 bg-white w-full z-0 hidden md:block text-gray-600">
                  <NavBreadCrumb
                    project={project.data}
                    dagTemplates={dagTemplateVersions.data}
                  />
                </div>
              )}
            <div className="mx-auto max-w-10xl sm:px-6 md:px-8">
              <div className="">{getElement()}</div>
            </div>
          </main>
        </div>
      </div>
    </>
  );
};

export default Dashboard;
