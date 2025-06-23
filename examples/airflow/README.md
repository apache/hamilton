# Apache Hamilton and Airflow

In this example, we're going to show how to run Apache Hamilton within a Airflow task. Both tools are used to author DAGs with Python code, but they operate on different levels:
- **Airflow** is an orchestrator written in Python. Its purpose is to launch tasks (which can be of any kind; Python, SQL, Bash, etc.) and make sure they complete.
- **Apache Hamilton** is a data transformation framework. It helps developer write Python code that is modular and reusable, and that can be executed as a DAG.

Therefore, Apache Hamilton allows you to write modular and easier to maintain code that can be used within or outside Airflow. This results in simpler Airflow DAG that will improve maintainability and might improve performance.

## File organization
- `/dags/hamilton/hamilton_how_to_dag.py` shows the basics of Apache Hamilton and illustrates how to integrate with Airflow.
- `/dags/hamilton/absenteeism_prediction_dag.py` shows a concrete example of loading data, training a machine learning model, and evaluating it.
- Each example is powered by Python modules under `/plugins/function_modules` and `/plugins/absenteeism` respectively (details about this in the How-to DAG). Under `/docs`, you'll find the DAG visualization of these Apache Hamilton modules.
- For the purpose of this example repository, data will be read from and written to `/plugins/data` since it is easily accessible to Airflow. This shouldn't be used in production settings.


## Airflow setup
We will use custom Docker containers based on the [official Airflow `docker-compose.yaml`](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html).

0. git clone the Apache Hamilton repository
1. From the terminal, go to the airflow example directory `hamilton/examples/airflow/`
2. Create a `.env` file with your Airflow UID using: `echo -e "AIRFLOW_UID=$(id -u)\nAIRFLOW_GID=0" > .env`
3. Create the Docker containers using: `docker compose up --build` This can take a few minutes. Afterwards, your Airflow Docker containers should be running.
4. Connect via `http://localhost:8080`. The default username is `airflow` and the password is `airflow`

## Motivation
1. **Simplify Airflow DAG**. Respect the ethos of Airflow [reference](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html#communication):

    Make your DAG generate simpler structure. Every task dependency adds additional processing overhead for scheduling and execution.
    The DAG that has simple linear structure A -> B -> C will experience less delays in task scheduling than DAG that has a deeply nested tree structure with exponentially growing number of depending tasks for example. If you can make your DAGs more linear - where at single point in execution there are as few potential candidates to run among the tasks, this will likely improve overall scheduling performance.


3. **Separate infrastructure from data science concerns**. Airflow is responsible for orchestrating tasks and is typically owned handled by data engineers. Apache Hamilton is responsible for authoring clean, reusable, and maintainable data transformations and is typically owned by data scientists. By integrating both tools, these two personas/teams have clearer ownership and version control over their codebases, and it can promote reusability of both Airflow and Apache Hamilton code. Notably, one can replace dynamic Airflow DAG (generated via config) by static Airflow DAG and let Apache Hamilton handle the dynamic data transformation requirements. This better separate the consistent Airflow infrastructure pipeline from the project specific Apache Hamilton data transforms. On the opposite, Apache Hamilton data transforms can be reused in Airflow pipelines to move data to power different initiatives (dashboard, app, API, etc.) greatly improving consistency.

4. **Write efficient Python code efficiently**. With Python being the 3rd most popular programming language in 2023, most data professionals should be able to pick up Airflow and Apache Hamilton quickly. However, production systems are composed of multiple services (database, datawarehouse, compute cluster, cache, serverless functions, etc.) most of which are SQL-based or have a Python SDK. This puts strains on engineers that need to learn and maintain this sprawling codebase. For orchestration, Airflow **providers** standardize interactions between the airflow DAG and external systems using the Python language ([see providers](https://registry.astronomer.io/providers)). For data transformation, Apache Hamilton **graph adapters** can automatically convert pandas code to production-grade computation engines such as Ray, Dask, Spark, Pandas on Spark (Koalas), Async Python ([see graph adapters (experimental)](https://hamilton.apache.org/reference/graph-adapters/)) These graph adapters automatically provide benefits such as result caching, GPU computing or out-of-core computation.


# Notes and limitations
- The edits to the default Airflow `docker-compose.yaml` file include:
    - building a custom Airflow image instead of pulling from Docker
    - Adding a graphviz backend to the Airflow image (see `Dockerfile`)
    - Installing Python packages in the Airflow image (see `Dockerfile`)
