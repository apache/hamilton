import { API_KEY_ICON } from "../Dashboard";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Link } from "react-router-dom";
import { useState } from "react";
import { classNames } from "../../../utils";
import { CheckBox } from "../../common/Checkbox";

const INSTALL_CODE = `# be sure to initialize any python environment you want to use first
pip install "sf-hamilton[sdk]"`;

const INSTALL_CODE_DW = `# be sure to initialize any python environment you want to use first
pip install dagworks-sdk`;

export const UsingHamiltonAlready = (props: {
  projectId: string | undefined;
  username: string;
  useHamiltonSDK: boolean;
}) => {
  const exampleCode = `
from ${props.useHamiltonSDK ? "hamilton_sdk" : "dagworks"} import adapters
from hamilton import driver
...
tracker = adapters.${props.useHamiltonSDK ? "HamiltonTracker": "DAGWorksTracker"}(
   project_id=${props.projectId},  # modify this as needed
   username="${props.username}",
   dag_name="my_version_of_the_dag",
   tags={"environment": "DEV", "team": "MY_TEAM", "version": "X"},
${props.useHamiltonSDK ? "":   '   api_key="your_api_key"'}
)
dr = (
  driver.Builder()
    .with_config(your_config)
    .with_modules(*your_modules)
    .with_adapters(tracker)
    .build()
)
# to run call .execute() or .materialize() on the driver
`;
  return (
    <>
      <li className="flex flex-col gap-2">
        <div className="flex flex-row gap-2 pt-2">
          <CheckBox />
          <p className="text-sm text-gray-500">
            Modify your regular Hamilton driver to log to the Hamilton UI:
          </p>
        </div>
        <SyntaxHighlighter language="python" style={vscDarkPlus}>
          {exampleCode}
        </SyntaxHighlighter>
      </li>
      <li>
        <div className="flex flex-row gap-2">
          <CheckBox />

          <p className="text-sm text-gray-500">
            Run your DAG. A new version will show up! Note that the versions are
            keyed on the &quot;dag_name&quot; as well as the code in the
            modules. you pass. No new version will be logged if neither of those
            change.
          </p>
        </div>
      </li>
    </>
  );
};

export const NotUsingHamiltonYet = (props: {
  projectId: string | undefined;
  username: string;
  useHamiltonSDK: boolean;
}) => {
  const initCode = props.useHamiltonSDK
      ? `git clone https://github.com/apache/hamilton.git
cd hamilton/examples/hamilton_ui
# provide the project ID and username for run.py.
`    : `git clone https://github.com/apache/dagworks-examples.git
cd dagworks-examples/hello_world/
# modify run.py -- change the username and project_id to your own
`;
  const pipCode = `pip install -r requirements.txt`;
  const runCode = props.useHamiltonSDK ? `python run.py` : `python run.py --api-key YOUR_API_KEY`;

  return (
    <>
      <li className="flex flex-col gap-2">
        <div className="flex flex-row gap-2 pt-2 items-center">
          <CheckBox />
          <p className="text-sm text-gray-500">
            Initialize the project from one of our demo project templates:
          </p>
        </div>
        <SyntaxHighlighter language="bash" style={vscDarkPlus}>
          {initCode}
        </SyntaxHighlighter>
      </li>
      <li className="flex flex-col gap-2">
        <div className="flex flex-row gap-2 pt-2 items-center">
          <CheckBox />
          <p className="text-sm text-gray-500">
            Install python dependencies for the example:
          </p>
        </div>
        <SyntaxHighlighter language="bash" style={vscDarkPlus}>
          {pipCode}
        </SyntaxHighlighter>
      </li>
      <li>
        <div className="flex flex-row gap-2 items-center">
          <CheckBox />

          <p className="text-sm text-gray-500">Run it!</p>
        </div>
        <SyntaxHighlighter language="bash" style={vscDarkPlus}>
          {runCode}
        </SyntaxHighlighter>
        <div className="flex flex-row gap-2 items-center">
          <CheckBox />

          {props.projectId !== undefined && (
            <p className="text-sm text-gray-500">
              <Link
                className="text-dwlightblue hover:underline"
                to={`/dashboard/project/${props.projectId}/runs`}
              >
                Track your runs!
              </Link>
            </p>
          )}
        </div>
      </li>
    </>
  );
};

export const ProjectLogInstructions = (props: {
  projectId?: number;
  username: string;
  canWrite: boolean;
  hideHeader?: boolean;
  hideAPIKey?: boolean;
}) => {
  const NOT_USING_HAMILTON = "Not Using Hamilton (yet)";
  const USING_HAMILTON = "Using Hamilton";
  const urlContainsDagworks = window.location.href.includes('app.dagworks.io');

  const tabs = [NOT_USING_HAMILTON, USING_HAMILTON];
  const [currentTab, setCurrentTab] = useState(tabs[1]);
  if (!props.canWrite) {
    return <NothingToSee />;
  }

  return (
    <div className="w-[90%]">
      <h1 className="text-xl font-semibold text-gray-700 px-5">
        Upload some runs!
      </h1>
      <ol className="px-5 mt-2">
        <li>
          <div className="flex flex-row gap-2 items-center">
            {!props.hideAPIKey && (
              <>
                <CheckBox />

                <p className="text-sm text-gray-500">
                  Get an API key from the left side menu (
                  <Link
                    to="/dashboard/settings"
                    className="inline-block hover:scale-110 text-dwlightblue"
                  >
                    <API_KEY_ICON />
                  </Link>
                  )
                </p>
              </>
            )}
          </div>
        </li>

        <li className="flex flex-col gap-2">
          <div className="flex flex-row gap-2">
            <CheckBox />
            <p className="text-sm text-gray-500 items-center">
              Install the SDK:
            </p>
          </div>
          <SyntaxHighlighter language="bash" style={vscDarkPlus}>
            {urlContainsDagworks ? INSTALL_CODE_DW : INSTALL_CODE}
          </SyntaxHighlighter>
        </li>
        <div>
          <div className="sm:hidden">
            <label htmlFor="tabs" className="sr-only">
              Select a tab
            </label>
            {/* Use an "onChange" listener to redirect the user to the selected tab URL. */}
            <select
              id="tabs"
              name="tabs"
              className="block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:border-dwdarkblue focus:outline-none focus:ring-dwdarkblue sm:text-sm cursor-pointer"
              defaultValue={tabs.find((tab) => tab === currentTab)}
            >
              {tabs.map((tab) => (
                <option key={tab}>{tab}</option>
              ))}
            </select>
          </div>
          <div className="hidden sm:block">
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex space-x-8" aria-label="Tabs">
                {tabs.map((tab) => (
                  <a
                    key={tab}
                    onClick={() => setCurrentTab(tab)}
                    className={classNames(
                      tab === currentTab
                        ? "border-dwlightblue text-dwlightblue"
                        : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 cursor-pointer",
                      "whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium"
                    )}
                    aria-current={tab === currentTab ? "page" : undefined}
                  >
                    {tab}
                  </a>
                ))}
              </nav>
            </div>
          </div>
          {currentTab === USING_HAMILTON ? (
            <UsingHamiltonAlready
              projectId={props.projectId?.toString()}
              username={props.username}
              useHamiltonSDK={!urlContainsDagworks}
            />
          ) : (
            <NotUsingHamiltonYet
              projectId={props.projectId?.toString()}
              username={props.username}
              useHamiltonSDK={!urlContainsDagworks}
            />
          )}
        </div>
      </ol>
    </div>
  );
};

export const NothingToSee = () => {
  return (
    <div className="w-[90%] flex justify-center ?">
      <h1 className="text-xl font-semibold text-gray-700 px-5 py-5">
        Nothing logged yet, check back later!
      </h1>
    </div>
  );
};
