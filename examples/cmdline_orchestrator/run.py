import os

from hamilton.execution.executors import MultiThreadingExecutor, SynchronousLocalTaskExecutor
from hamilton.experimental.h_cache import CachingGraphAdapter

if __name__ == "__main__":
    import funcs
    from cmdline import CMDLineExecutionManager
    from dagworks import adapters

    from hamilton import driver

    tracker = adapters.DAGWorksTracker(
        username="stefan@dagworks.io",
        api_key=os.environ["DAGWORKS_API_KEY"],
        project_id=os.environ["DAGWORKS_PROJECT_ID"],
        dag_name="toy-cmdline-dag",
        tags={"env": "local"},  # , "TODO": "add_more_tags_to_find_your_run_later"},
    )

    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_execution_manager(
            CMDLineExecutionManager(SynchronousLocalTaskExecutor(), MultiThreadingExecutor(5))
        )
        .with_modules(funcs)
        .with_adapters(
            tracker,
            CachingGraphAdapter("./cache"),
            #            PrintLnHook()
        )
        .build()
    )
    dr.display_all_functions("graph.dot")
    print(dr.list_available_variables())
    # for var in dr.list_available_variables():
    #     print(dr.execute([var.name], inputs={"start": "hello"}))
    print(dr.execute(["echo_3"], inputs={"start": "hello"}))
