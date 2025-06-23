# Apache Hamilton UI - Machine learning example

Learn how to use the `HamiltonTracker` and the Apache Hamilton UI to track a simple machine learning pipeline.

It also illustrates the following notions:

1. Splitting a pipeline into separate modules (e.g., data loading, feature enginering, model fitting)
2. Use `DataLoader` and `DataSaver` objects to load & save data and collect extra metadata in the UI
3. Use `@subdag` to fit different ML models with the same model training code in the same DAG run.


## Getting started
### Install the Apache Hamilton UI

First, you need to have the Apache Hamilton UI running. You can either `pip install` the Apache Hamilton UI (recommended) or run it as a Docker container.

#### Local Install
Install the Python dependencies:

```bash
pip install "sf-hamilton[ui,sdk]"
```
then launch the Apache Hamilton UI server:
```bash
hamilton ui
# python -m hamilton.cli.__main__ ui # on windows
```

#### Docker Install

See https://hamilton.apache.org/concepts/ui/ for details, here are the cliff notes:

```bash
git clone https://github.com/apache/hamilton
cd hamilton/ui/deployment
./run.sh
```
Then go to http://localhost:8242 to create (1) a username and (2) a project.
See [this video](https://youtu.be/DPfxlTwaNsM) for a walkthrough.

### Execute and track the pipeline

Now that you have the Apache Hamilton UI running, open another terminal tab to:

1. Ensure you have the right python dependencies installed.
```bash
cd hamilton/examples/hamilton_ui
pip install -r requirements.txt
```

2. Run the `run.py` script. Providing the username and project ID to be able to log to the Apache Hamilton UI.
```bash
python run.py --username <username> --project_id <project_id>
```
Once you've run that, run this:
```bash
python run.py --username <username> --project_id <project_id> --load-from-parquet
```

3. Explore results in the Apache Hamilton UI. Find your project under http://localhost:8242/dashboard/projects.

## Things to try:

1. Place an error in the code and see how it shows up in the Apache Hamilton UI. e.g. `raise ValueError("I'm an error")`.
2. In `models.py` change `"data_set": source("data_set_v1"),` to `"data_set": source("data_set_v2"),`, along with
what is requested in `run.py` (i.e. change/add saving `data_set_v2`) and see how the lineage changes in the Apache Hamilton UI.
3. Add a new feature and propagate it through the pipeline. E.g. add a new feature to `features.py` and then to a dataset.
Execute it and then compare the data observed in the Apache Hamilton UI against a prior run.
