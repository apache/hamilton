======================
Airflow
======================

For more details see this `Apache Hamilton + Airflow blog post <https://blog.dagworks.io/p/supercharge-your-airflow-dag-with>`_.

**TL;DR:**

1. Apache Hamilton complements Airflow. It'll help you write better, more modular, and testable code.
2. Apache Hamilton does not replace Airflow.


High-level differences:
-----------------------

* Apache Hamilton is a micro-orchestator. Airflow is a macro-orchestrator.
* Apache Hamilton is a Python library standardizing how you express python pipelines, while Airflow is a complete platform and
  system for scheduling and executing pipelines.
* Apache Hamilton focuses on providing a lightweight, low dependency, flexible way to define data pipelines as Python functions,
  whereas Airflow is a whole system that comes with a web-based UI, scheduler, and executor.
* Apache Hamilton pipelines are defined using pure Python code, that can be run anywhere that Python runs. While Airflow uses
  Python to describe a DAG, this DAG can only be run by the Airflow system.
* Apache Hamilton complements Airflow, and you can use Apache Hamilton within Airflow. But the reverse is not true.
* You can use Apache Hamilton directly in a Jupyter Notebook, or Python web-service. You can't do this with Airflow.


Code examples:
--------------
Looking at the two examples below, you can see that Apache Hamilton is a more lightweight and flexible way to define data pipelines.
There is no scheduling information, etc required to run the code because Apache Hamilton runs the pipeline in the same process as the
caller. This makes it easier to test and debug pipelines. Airflow, on the other hand, is a complete system for scheduling and
executing pipelines. It is more complex to set up and run. Note: If you stuck the contents of `run.py` in a function within
the `example_dag.py`, the Apache Hamilton pipeline could be used in the Airflow PythonOperator!

Apache Hamilton:
________________
The below code here shows how you can define a simple data pipeline using Apache Hamilton. The pipeline consists of three functions
that are executed in sequence. The pipeline is defined in a module called `pipeline.py`, and then executed in a separate
script called `run.py`, which imports the pipeline module and executes it.

.. code-block:: python

    # pipeline.py
    def raw_data() -> list[int]:
        return [1, 2, 3]

    def processed_data(raw_data: list[int]) -> list[int]:
        return [x * 2 for x in data]

    def load_data(process_data: list[int], client: SomeClient) -> dict:
        metadata = client.send_data(process_data)
        return metadata

    # run.py -- this is the script that executes the pipeline
    import pipeline
    from hamilton import driver
    dr = driver.Builder().with_modules(pipeline).build()
    metadata = dr.execute(['load_data'], inputs=dict(client=SomeClient()))

Airflow:
________
The below code shows how you can define the same pipeline using Airflow. The pipeline consists of three tasks that are executed
in sequence. The entire pipeline is defined in a module called `example_dag.py`, and then executed by the Airflow scheduler.

.. code-block:: python

    # example_dag.py
    from airflow import DAG
    from airflow.operators.python_operator import PythonOperator
    from datetime import datetime, timedelta

    default_args = {
        'owner': 'airflow',
        'depends_on_past': False,
        'start_date': datetime(2023, 1, 1),
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
    }

    dag = DAG(
        'example_dag',
        default_args=default_args,
        description='A simple DAG',
        schedule_interval=timedelta(days=1),
    )

    def extract_data():
        return [1, 2, 3]

    def transform_data(data):
        return [x * 2 for x in data]

    def load_data(data):
        client = SomeClient()
        client.send_data(data)

    extract_task = PythonOperator(
        task_id='extract_data',
        python_callable=extract_data,
        dag=dag,
    )

    transform_task = PythonOperator(
        task_id='transform_data',
        python_callable=transform_data,
        op_args=['{{ ti.xcom_pull(task_ids="extract_data") }}'],
        dag=dag,
    )

    load_task = PythonOperator(
        task_id='load_data',
        python_callable=load_data,
        op_args=['{{ ti.xcom_pull(task_ids="transform_data") }}'],
        dag=dag,
    )

    extract_task >> transform_task >> load_task



