import os.path

import pytest
from hamilton_sdk import adapters

from hamilton import driver

import tests.resources.basic_dag_with_config
import tests.resources.parallel_dag
import tests.resources.parallel_dag_error
from tests import test_tracking

adapter_kwargs = dict(
    project_id=19319,
    api_key="l-PlUq02JLQR6rAvO4x7VTttNTtprj1Tz5zBZ0ARpQ4olb8TK4hlgY2pennFhvsR1DxpYMQ-TLm0JknXVn7y9A",
    username="stefank@cs.stanford.edu",
    tags={"env": "dev", "status": "development"},
    client_factory=test_tracking.MockHamiltonClient,
)


def test_adapters():
    kwargs = adapter_kwargs | dict(
        dag_name="test_dag",
    )
    lifecycle_adapters = [adapters.HamiltonTracker(**kwargs)]
    dr = (
        driver.Builder()
        .with_modules(tests.resources.basic_dag_with_config)
        .with_config({"foo": "baz"})
        .with_adapters(*lifecycle_adapters)
        .build()
    )
    result = dr.execute(final_vars=["a", "b", "c"], inputs={"a": 1})
    assert result == {"a": 1, "b": 3, "c": 6}


# def test_async():
#     # TODO: complete Async
#     kwargs = adapter_kwargs | dict(
#         dag_name="async_test_dag",
#     )
#     [adapters.AsyncHamiltonAdapter(**kwargs)]


def test_parallel_ray():
    """Tests ray works without sampling.
    Doesn't actually check the client - go do that in the UI."""
    import ray

    from hamilton.plugins import h_ray

    kwargs = adapter_kwargs | dict(dag_name="parallel_test_dag", tags={"sampling_rate": "None"})
    lifecycle_adapters = [adapters.HamiltonTracker(**kwargs)]
    remote_executor = h_ray.RayTaskExecutor(None)
    # remote_executor = executors.SynchronousLocalTaskExecutor()
    shutdown = ray.shutdown
    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(remote_executor)  # We only need to specify remote executor
        # The local executor just runs it synchronously
        .with_modules(tests.resources.parallel_dag)
        .with_adapters(*lifecycle_adapters)
        .build()
    )
    data_dir = os.path.join(os.path.dirname(__file__), "resources", "data")
    result = dr.execute(final_vars=["statistics_by_city"], inputs={"data_dir": data_dir})[
        "statistics_by_city"
    ]
    print(result)
    if shutdown:
        shutdown()
    expected_cities = {"barcelona", "berlin", "budapest"}
    for val in result.index.values:
        assert val in expected_cities


def test_parallel_ray_sample():
    """Tests ray works with sampling.
    Doesn't actually check the client - go do that in the UI."""
    import ray

    from hamilton.plugins import h_ray

    special_parallel_sample_strategy = 0.33
    kwargs = adapter_kwargs | dict(
        dag_name="parallel_test_dag", tags={"sampling_rate": str(special_parallel_sample_strategy)}
    )
    lifecycle_adapters = [adapters.HamiltonTracker(**kwargs)]
    lifecycle_adapters[0].special_parallel_sample_strategy = special_parallel_sample_strategy
    remote_executor = h_ray.RayTaskExecutor(None)
    # remote_executor = executors.SynchronousLocalTaskExecutor()
    shutdown = ray.shutdown
    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(remote_executor)  # We only need to specify remote executor
        # The local executor just runs it synchronously
        .with_modules(tests.resources.parallel_dag)
        .with_adapters(*lifecycle_adapters)
        .build()
    )
    data_dir = os.path.join(os.path.dirname(__file__), "resources", "data")
    result = dr.execute(final_vars=["statistics_by_city"], inputs={"data_dir": data_dir})[
        "statistics_by_city"
    ]
    print(result)
    if shutdown:
        shutdown()
    expected_cities = {"barcelona", "berlin", "budapest"}
    for val in result.index.values:
        assert val in expected_cities


def test_parallel_ray_sample_error():
    """Tests error returning a sample.
    Doesn't actually check the client - go do that in the UI."""
    import ray

    from hamilton.plugins import h_ray

    special_parallel_sample_strategy = 0.0
    kwargs = adapter_kwargs | dict(
        dag_name="parallel_test_dag", tags={"sampling_rate": str(special_parallel_sample_strategy)}
    )
    lifecycle_adapters = [adapters.HamiltonTracker(**kwargs)]
    lifecycle_adapters[0].special_parallel_sample_strategy = special_parallel_sample_strategy
    remote_executor = h_ray.RayTaskExecutor(None)
    # remote_executor = executors.SynchronousLocalTaskExecutor()
    shutdown = ray.shutdown
    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(remote_executor)  # We only need to specify remote executor
        # The local executor just runs it synchronously
        .with_modules(tests.resources.parallel_dag_error)
        .with_adapters(*lifecycle_adapters)
        .build()
    )
    data_dir = os.path.join(os.path.dirname(__file__), "resources", "data")
    with pytest.raises(ValueError):
        dr.execute(final_vars=["statistics_by_city"], inputs={"data_dir": data_dir})
    if shutdown:
        shutdown()


if __name__ == "__main__":
    # test_adapters()

    # logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    # test_async()
    # test_parallel_ray_sample()
    # test_parallel_ray()
    test_parallel_ray_sample_error()
