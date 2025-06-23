import { IconType } from "react-icons";
import {
  AiOutlinePhone,
  AiOutlinePlayCircle,
  AiOutlineProject,
} from "react-icons/ai";
import { GiPlatform } from "react-icons/gi";
import { LoomHelpVideo } from "../tutorial/HelpVideo";
import { Link } from "react-router-dom";
import { CheckBox } from "../common/Checkbox";
import { BiChevronDown, BiChevronUp, BiNetworkChart } from "react-icons/bi";
import { useState } from "react";
import { classNames } from "../../utils";
import {
  AttributeDocumentationLoom1,
  getProjectAttributes,
  useProjectByID,
} from "../../state/api/friendlyApi";
import { Loading } from "../common/Loading";
import { ErrorPage } from "../common/Error";
import { ProjectDocumentation } from "./Project/ProjectDocumentation";
import { FiExternalLink } from "react-icons/fi";
import { PostHog, usePostHog } from "posthog-js/react";
import { skipToken } from "@reduxjs/toolkit/dist/query";

const WelcomeCard = (props: {
  id: string;
  title: string;
  expectedTime?: string;
  children: JSX.Element | JSX.Element[];
  Icon: IconType;
  expanded: boolean;
  setOpen: () => void;
  setClosed: () => void;
  subheader?: boolean;
  alternate?: {
    title: string;
    onClick: () => void;
  };
}) => {
  const posthog = usePostHog();
  const isSubheader = props.subheader || false;
  const ExpandIcon = props.expanded ? BiChevronUp : BiChevronDown;
  const onClick = (step: string, posthog: PostHog | undefined) => {
    if (props.expanded) {
      props.setClosed();
    }
    if (!props.expanded) {
      posthog?.capture("click-welcome-step", { step: step });
      props.setOpen();
    }
  };
  const font = isSubheader ? "font-normal" : "font-semibold";
  return (
    <div className="divide-y h-full w-full divide-gray-200 overflow-hidden rounded-lg bg-white shadow-md hover:bg-dwdarkblue/5">
      <div
        className={`px-4 py-5 sm:px-6 ${font} flex flex-row gap-2 text-gray-800 justify-between items-center`}
        onClick={() => onClick(props.id, posthog)}
      >
        <div className="flex flex-row gap-2 items-center">
          <props.Icon className="text-3xl  hover:scale-110" />
          <span className={`${props.expanded ? "underline" : ""} text-xl`}>
            {props.title}
          </span>
          {props.expectedTime ? (
            <span className="font-normal text-gray-400">
              ({props.expectedTime})
            </span>
          ) : (
            <></>
          )}
          {props.alternate ? (
            <>
              <span className="text text-gray-400">or</span>{" "}
              <span
                className="text-dwlightblue hover:underline cursor-pointer"
                onClick={
                  props.alternate
                    ? (e) => {
                        props.alternate?.onClick();
                        e.preventDefault();
                        e.stopPropagation();
                      }
                    : () => void 0
                }
              >
                {props.alternate.title}
              </span>
            </>
          ) : (
            <></>
          )}
        </div>
        {/* We use less vertical padding on card headers on desktop than on body sections */}
        <ExpandIcon className="text-3xl" />
      </div>
      {props.expanded ? (
        <div className="px-4 py-5 sm:p-6 text-gray-700 h-full">
          {props.children}
        </div>
      ) : null}
    </div>
  );
};

export const DemoProjectSelector = (props: {
  projects: {
    name: string;
    projectID: number;
  }[];
}) => {
  const [currentTab, setCurrentTab] = useState(0);
  const projectId = props.projects[currentTab].projectID;
  const project = useProjectByID(
    projectId !== undefined
      ? {
          projectId: projectId,
          attributeTypes: ["documentation_loom"].join(","),
        }
      : skipToken
  );

  //   const project = useProjectByID({
  //     projectId: props.projects[currentTab].projectID,
  //   });
  const loading = project.isLoading || project.isFetching;
  const error = project.isError || project.isUninitialized;

  const loomDocs = getProjectAttributes<AttributeDocumentationLoom1>(
    project.data?.attributes || [],
    "AttributeDocumentationLoom1"
  );

  return (
    <div className="w-full">
      <div className="sm:hidden">
        <label htmlFor="tabs" className="sr-only">
          Select a tab
        </label>
        <select
          id="tabs"
          name="tabs"
          className="block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
          defaultValue={
            props.projects.find((project, i) => currentTab === i)?.name
          }
        >
          {props.projects.map((project) => (
            <option key={project.name}>{project.name}</option>
          ))}
        </select>
      </div>
      <div className="hidden sm:block">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            {props.projects.map((project, i) => (
              <a
                onClick={() => setCurrentTab(i)}
                key={project.name}
                className={classNames(
                  currentTab === i
                    ? "border-dwdarkblue text-dwdarkblue"
                    : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700",
                  "whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium cursor-pointer flex flex-row items-center gap-2"
                )}
                aria-current={currentTab === i ? "page" : undefined}
              >
                {props.projects[i].name}{" "}
                <Link to={`/dashboard/project/${project.projectID}`}>
                  <FiExternalLink className="inline hover:scale-125 text-dwlightblue" />
                </Link>
              </a>
            ))}
          </nav>
        </div>
      </div>
      <>
        {loading ? (
          <div className="p-2">
            <Loading />
          </div>
        ) : error ? (
          <ErrorPage message={""} />
        ) : loomDocs.length === 0 ? (
          // TODO -- replace with real one
          <div className="pl-20 pt-10 pb-10">
            <span>Video coming soon!</span>
          </div>
        ) : (
          <ProjectDocumentation loomDocs={loomDocs} />
        )}
      </>
    </div>
  );
};

export const Welcome = () => {
  /**
   * Just some divs to represent home/navigation
   * TODO -- delete me. I'm unecessary past rudimentary development.
   */

  const onboardingItems = [
    {
      identifier: "platform-overview",
      title: "Platform overview",
      expectedTime: "1 minute",
      Icon: GiPlatform,
      contents: (
        <div className="h-[550px]">
          <LoomHelpVideo
            loomId="5c2c25e7bcc247d3a10f478b42ce4655"
            height="100%"
            width="100%"
          />
        </div>
      ),
      alternate: {
        title: "skip ahead to get started!",
        onClick: () => {
          setWhichExpanded(2);
        },
      },
    },
    {
      identifier: "why-use-dagworks",
      title: "Why use the DAGWorks platform?",
      expectedTime: "5-15 minutes",
      Icon: AiOutlineProject,
      contents: (
        <div className="flex flex-col gap-2">
          <ul className="pt-2">
            <li className="leading-8">
              Getting data and ML/AI pipelines to production is easy when you’re
              small, but when your team and codebase start to grow, maintaining
              these pipelines becomes challenging:
              <ul className="list-disc list-inside pl-4">
                <li>😕 understanding code you didn’t write</li>
                <li>🐛 debugging production issues</li>
                <li>🏗️ migrating to new infrastructure</li>
                <li>🥼 handling personnel changes</li>
              </ul>
              Here we present a series of quick videos that demonstrate how
              DAGWorks can help you overcome these challenges by using Hamilton
              dataflows together with the DAGWorks platform.
              <br />
              Each video uses one of several demo projects to demonstrate
              capabilities such as: code &amp; data observability, lineage, and
              cataloging; which we invite you to explore in more detail after
              watching the videos.
            </li>
            <li className="flex flex-wrap items-center gap-2 pt-2">
              <CheckBox /> Watch the three minute &apos;Hello World Platform
              Overview&apos; video (first video 👇).
            </li>
            <li className="flex flex-wrap items-center gap-2">
              <CheckBox />
              Watch the demo project videos most relevant to your day to day (or
              watch them all!){" "}
            </li>
            <li className="flex flex-wrap items-center gap-2">
              <CheckBox />
              Explored a demo project(s) in more detail.
            </li>
          </ul>
          <div className="flex flex-wrap">
            <DemoProjectSelector
              projects={[
                {
                  name: "Hello World Platform Overview",
                  projectID: 2,
                },
                {
                  name: "Pandas Data Processing",
                  projectID: 42,
                },
                {
                  name: "Time series feature engineering",
                  projectID: 31,
                },
                {
                  name: "Machine learning",
                  projectID: 29,
                },

                //...
              ]}
            />
          </div>
        </div>
      ),
    },
    {
      identifier: "integrate-with-dagworks",
      title: "Integrate with the DAGWorks Platform",
      Icon: BiNetworkChart,
      expectedTime: "5 minutes",
      contents: (
        <ul>
          {" "}
          <li className="flex flex-wrap items-center gap-1">
            <span className="mr-1 mb-1">
              <CheckBox />{" "}
            </span>
            Navigate to the
            <Link
              target="_blank"
              className="hover:underline text-dwlightblue"
              to="/dashboard/projects/"
            >
              {" "}
              projects page{" "}
            </Link>{" "}
            and create a{" "}
            <Link
              target="_blank"
              className=""
              to="/dashboard/projects/?new=true"
            >
              <span className="text-white bg-green-500 px-2 rounded-lg">
                + New Project
              </span>
            </Link>
            .
          </li>
          {/* We don't have the facility to invite -- so dropping mentioning it here */}
          {/*<li className="flex flex-wrap items-center gap-1">*/}
          {/*  <span className="mr-1 mb-1">*/}
          {/*    <CheckBox />{" "}*/}
          {/*  </span>*/}
          {/*  Set project visibility to yourself or your team (let us know who to invite to give them access).*/}
          {/*</li>*/}
          <li className="flex flex-wrap items-center gap-1">
            <span className="mr-1 mb-1">
              <CheckBox />{" "}
            </span>
            Follow the instructions to integrate with your existing Hamilton
            code, or get started with one of our demo templates.
          </li>
          <li className="flex flex-wrap items-center gap-1">
            <span className="mr-1 mb-1">
              <CheckBox />{" "}
            </span>
            Execute your Hamilton code connecting the DAGWorks Tracking Adapter
            with the Hamilton Driver.
          </li>
          <li className="flex flex-wrap items-center gap-1">
            <span className="mr-1 mb-1">
              <CheckBox />{" "}
            </span>
            Select your project on{" "}
            <Link
              target="_blank"
              className="hover:underline text-dwlightblue"
              to="/dashboard/projects/"
            >
              {" "}
              the projects page{" "}
            </Link>
            and view information about your Hamilton dataflow!
          </li>
          <li className="flex flex-wrap items-center gap-1">
            <span className="mr-1 mb-1">
              <CheckBox />{" "}
            </span>
            [For reference] Familiarise yourself with our platform{" "}
            <a
              target="_blank"
              rel="noreferrer"
              className="hover:underline text-dwlightblue"
              href="https://docs.dagworks.io"
            >
              {" "}
              documentation.
            </a>
          </li>
        </ul>
      ),
    },
    {
      identifier: "get-up-to-speed-on-hamilton",
      title: "Get up to speed on Hamilton",
      Icon: AiOutlinePlayCircle,
      expectedTime: "5+ minutes",
      contents: (
        <>
          <span className="py-2">
            To reap the benefits of the DAGWorks Platform you need to be using
            Hamilton. Here&apos;s a few ways to get up to speed:
          </span>
          <li className="flex flex-wrap items-center gap-1">
            <span className="mr-1 mb-1">
              <CheckBox />{" "}
            </span>
            Exercise the basics of Hamilton
            <a
              target="_blank"
              rel="noreferrer"
              className="hover:underline text-dwlightblue"
              href="https://www.tryhamilton.dev"
            >
              in your browser.
            </a>
          </li>

          <li className="flex flex-wrap items-center gap-1">
            <span className="mr-1 mb-1">
              <CheckBox />{" "}
            </span>
            Familiarize yourself with
            <a
              target="_blank"
              rel="noreferrer"
              className="hover:underline text-dwlightblue"
              href="https://hamilton.apache.org"
            >
              Hamilton&apos;s documentation and examples.
            </a>
          </li>
          <li className="flex flex-wrap items-center gap-1">
            <span className="mr-1 mb-1">
              <CheckBox />{" "}
            </span>
            Star ⭐️ the
            <a
              target="_blank"
              rel="noreferrer"
              className="hover:underline text-dwlightblue"
              href="https://www.github.com/dagworks-inc/hamilton"
            >
              Hamilton repository.
            </a>
          </li>
          <li className="flex flex-wrap items-center gap-1">
            <span className="mr-1 mb-1">
              <CheckBox />{" "}
            </span>
            [Optional]
            <a
              target="_blank"
              rel="noreferrer"
              className="hover:underline text-dwlightblue"
              href="https://calendly.com/stefan-dagworks/dagworks-help"
            >
              Book time
            </a>
            with us to learn more!
          </li>
        </>
      ),
    },
    {
      identifier: "contact-us",
      title: "Contact us for help/feedback",
      Icon: AiOutlinePhone,
      expectedTime: "2 minutes",
      contents: (
        <span>
          We&apos;re really excited about Hamilton and what we&apos;re building
          at DAGWorks. <br />
          <br />
          If you want help making the most of the DAGWorks Platform, or have
          feedback on what we could improve or add to make it better for you,
          you can:{" "}
          <ul className="list-disc pl-4">
            <li className="pt-3 pb-3">
              ✉️{" "}
              <a
                className="text-dwlightblue hover:underline"
                href="mailto:support@dagworks.io"
              >
                email
              </a>{" "}
              us anytime
            </li>
            <li className="pb-3">
              join us on{" "}
              <a
                className="text-dwlightblue hover:underline"
                href="https://join.slack.com/t/dagworks-platform/shared_invite/zt-1zok0nfh0-sfgX62HFHDcAb~jEsdTRjQ"
              >
                slack
              </a>
            </li>
            <li className="pb-1">
              📞{" "}
              <a
                className="text-dwlightblue hover:underline"
                href="tel:+15109195369"
              >
                call us
              </a>
            </li>
            <li>
              or simply use the{" "}
              <button
                data-feedback-fish="true"
                data-feedback-fish-url={window.location.href}
                // data-feedback-fish-userid={props.userName}
                data-feedback-fish-location="welcome-feedback-button"
                className="opacity-90 hover:opacity-100 hover:shadow-xl cursor-pointer shadow-lg rounded-full bg-yellow-400 py-2 px-5 text-gray-900"
              >
                feedback
              </button>{" "}
              button!
            </li>
          </ul>
        </span>
      ),
    },
  ];
  const [whichExpanded, setWhichExpanded] = useState<number>(0);
  const setNext = () => {
    setWhichExpanded((whichExpanded + 1) % onboardingItems.length);
  };
  const set = (i: number) => {
    setWhichExpanded(i);
  };

  return (
    <div className="max-w-9xl flex flex-col gap-5 pt-10">
      <div className="flex flex-col w-full">
        <h1 className="text-4xl font-semibold text-center">
          Welcome to the DAGWorks Platform (beta!)
        </h1>
      </div>
      <div className="flex flex-col gap-4 w-full">
        {onboardingItems.map((task, index) => (
          <WelcomeCard
            id={task.identifier}
            expectedTime={task.expectedTime}
            key={index}
            title={`Step ${index + 1}: ${task.title}`}
            Icon={task.Icon}
            setOpen={() => {
              set(index);
            }}
            setClosed={() => {
              setNext();
            }}
            expanded={whichExpanded === index}
            alternate={task?.alternate}
          >
            {task.contents}
          </WelcomeCard>
        ))}
      </div>
    </div>
  );
};
