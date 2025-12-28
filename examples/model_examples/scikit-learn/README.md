<!--
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
-->

# Using Apache Hamilton for ML dataflows

Here we have a simple example showing how you can
write a ML training and evaluation workflow with Apache Hamilton.

`pip install scikit-learn` or `pip install -r requirements.txt` to get the right python dependencies
to run this example.

## Reusable general logic
* `my_train_evaluate_logic.py` houses logic that should be invariant to how hamilton is executed. This contains logic
written in a reusable way.

You can think of the 'inputs' to the functions here, as an interface a "data loading" module would have to fulfill.

## data loaders
* `iris_loader.py` houses logic to load iris data.
* `digit_loader.py` houses logic to load digit data.

The idea is that you'd swap these modules out/create new ones that would dictate what data is loaded.
Thereby enabling you to create the right inputs into your dataflow at DAG construction time. They should
house the same function names as they should map to the inputs required by functions defined in `my_train_evaluate_logic.py`.

## running it
* run.py houses the "driver code" required to stitch everything together. It is responsible for creating the
right configuration to create the DAG, as well as determining what python modules should be loaded.

You can even run this example in Google Colab:
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)
](https://colab.research.google.com/github/dagworks-inc/hamilton/blob/main/examples/model_examples/scikit-learn/Hamilton_for_ML_dataflows.ipynb)


# Visualization of execution
Here is the graph of execution for the digits data set and logistic regression model:

![model_dag_digits_logistic.dot.png](model_dag_digits_logistic.dot.png)

Here is the graph of execution for the iris data set and SVM model:

![model_dag_iris_svm](model_dag_iris_svm.dot.png)
