# Import Community Dataflows

In this example, we show you how to import and use dataflows from the [Apache Hamilton Dataflow Hub](https://hub.dagworks.io/docs/).
You can use them either directly or pull and edit a local copy.

# Setup
For the purpose of this example, we will create a virtual environment with hamilton, the hamilton contrib module, and the requirements for the dataflow we'll import.
1. `python -m venv ./venv`
2. `. venv/bin/activate` (on MacOS / Linux) or `. venv/bin/Scripts` (Windows)
3. `pip install -r requirements.txt`

Or run it in Google Colab:
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)
](https://colab.research.google.com/github/dagworks-inc/hamilton/blob/main/examples/contrib/notebook.ipynb)


# 3 ways to import
There are 3 main ways to use community dataflows: static installation, dynamic installation, and local copy (see [documentation](https://github.com/apache/hamilton/tree/main/contrib)). We present each of them in this example:

## 1. Static installation
The script `run.py` uses the direct import `from hamilton.contrib.user.zilto import xgboost_optuna`. It's as simple as that! (but first `pip install sf-hamilton-contrib --upgrade`)

## 2. Dynamic installation
The first part of the notebook `notebook.ipynb` imports the same dataflow via `xgboost_optuna = hamilton.dataflows.import_module("xgboost_optuna", "zilto")`. This will download and cache the module in your local directory `{USER_PATH}/.hamilton`.

## 3. Local copy
After completing the dynamic installation, the second part of the notebook includes `hamilton.dataflows.copy(xgboost_optuna, destination_path="./my_local_path")` will create a local copy at the desire location. Then, you'll be able to do `from my_local_path import xgboost_optuna`.


# Contribute your own dataflow!
You can find more information on how to contribute in the `contrib` module's [README](https://github.com/apache/hamilton/tree/main/contrib)
